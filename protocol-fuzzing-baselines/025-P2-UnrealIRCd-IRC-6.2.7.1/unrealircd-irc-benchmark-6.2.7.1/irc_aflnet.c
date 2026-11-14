/* AFLNet adapter for plaintext IRC client/server messages over TCP.
 * One CRLF-delimited client line is a request region. Numeric server
 * replies and common command replies are mapped to stable state IDs. */
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

static void irc_append_region(region_t **regions, unsigned int *count,
                              unsigned int start, unsigned int end)
{
  *regions = (region_t *)ck_realloc(*regions, (*count + 1) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

region_t *extract_requests_irc(unsigned char *buf, unsigned int buf_size,
                               unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0, start = 0, i;

  if (!buf || !buf_size) {
    *region_count_ref = 0;
    return NULL;
  }

  for (i = 0; i + 1 < buf_size; i++) {
    if (buf[i] == '\r' && buf[i + 1] == '\n') {
      irc_append_region(&regions, &count, start, i + 1);
      start = i + 2;
      i++;
    }
  }
  /* Keep an incomplete final command as one region for malformed-input tests. */
  if (start < buf_size)
    irc_append_region(&regions, &count, start, buf_size - 1);

  *region_count_ref = count;
  return regions;
}

static int irc_equal(const unsigned char *buf, unsigned int start,
                     unsigned int end, const char *word)
{
  unsigned int i, length = (unsigned int)strlen(word);
  if (end - start != length) return 0;
  for (i = 0; i < length; i++) {
    unsigned char c = buf[start + i];
    if (c >= 'a' && c <= 'z') c = (unsigned char)(c - 'a' + 'A');
    if (c != (unsigned char)word[i]) return 0;
  }
  return 1;
}

static unsigned int irc_command_state(const unsigned char *buf,
                                      unsigned int start, unsigned int end)
{
  static const char *const commands[] = {
    "CAP", "ERROR", "JOIN", "NOTICE", "PART", "PING", "PONG",
    "PRIVMSG", "QUIT", "TOPIC", "NICK", "MODE", "ACCOUNT", "AWAY",
    "AUTHENTICATE", "BATCH", "FAIL", "WARN", "NOTE", "TAGMSG",
    "KICK", "INVITE", "CHGHOST", "SETNAME", "WHO", "NAMES", "LIST",
    "WHOIS", "WHOWAS", "MOTD", "VERSION", "TIME", "ADMIN", "LUSERS"
  };
  unsigned int i, j, hash = 2166136261u;
  for (i = 0; i < sizeof(commands) / sizeof(commands[0]); i++)
    if (irc_equal(buf, start, end, commands[i])) return 2001u + i;

  /* Stable fallback for future/extension commands, independent of process. */
  for (j = start; j < end; j++) {
    unsigned char c = buf[j];
    if (c >= 'a' && c <= 'z') c = (unsigned char)(c - 'a' + 'A');
    hash = (hash ^ c) * 16777619u;
  }
  return 100000u + hash % 1000000u;
}

static unsigned int irc_response_state(const unsigned char *buf,
                                       unsigned int start, unsigned int end)
{
  unsigned int i, command_start, command_end, number = 0;

  /* IRCv3 tags: @key=value ... <space> */
  if (start < end && buf[start] == '@') {
    while (start < end && buf[start] != ' ') start++;
    if (start == end) return 999999u;
    while (start < end && buf[start] == ' ') start++;
  }
  /* Optional server/user prefix: :prefix <space> */
  if (start < end && buf[start] == ':') {
    while (start < end && buf[start] != ' ') start++;
    if (start == end) return 999999u;
    while (start < end && buf[start] == ' ') start++;
  }
  command_start = start;
  while (start < end && buf[start] != ' ') start++;
  command_end = start;
  if (command_start == command_end) return 999999u;

  if (command_end - command_start == 3) {
    for (i = command_start; i < command_end; i++) {
      if (buf[i] < '0' || buf[i] > '9') break;
      number = number * 10 + (unsigned int)(buf[i] - '0');
    }
    if (i == command_end) return 1000u + number;
  }
  return irc_command_state(buf, command_start, command_end);
}

static void irc_append_state(unsigned int **states, unsigned int *count,
                             unsigned int state)
{
  *states = (unsigned int *)ck_realloc(*states,
                                       (*count + 1) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

unsigned int *extract_response_codes_irc(unsigned char *buf,
                                         unsigned int buf_size,
                                         unsigned int *state_count_ref)
{
  unsigned int *states = NULL, count = 0, start = 0, i;
  irc_append_state(&states, &count, 0); /* Initial protocol state. */

  if (buf) {
    for (i = 0; i + 1 < buf_size; i++) {
      if (buf[i] == '\r' && buf[i + 1] == '\n') {
        if (i > start)
          irc_append_state(&states, &count, irc_response_state(buf, start, i));
        start = i + 2;
        i++;
      }
    }
    /* An unfinished server line may be a transport fragment; do not turn it
     * into a fake protocol state. Only complete CRLF lines are feedback. */
  }

  *state_count_ref = count;
  return states;
}
