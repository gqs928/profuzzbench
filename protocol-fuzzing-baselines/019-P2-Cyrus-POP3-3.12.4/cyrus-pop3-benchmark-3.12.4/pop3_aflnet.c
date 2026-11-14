/* POP3 request framing and stable status-code feedback for AFLNet. */
#include <ctype.h>
#include <limits.h>
#include <stddef.h>
#include <string.h>
#include <sys/time.h>

#include "alloc-inl.h"
#include "aflnet.h"

static void pop3_add_region(region_t **regions, unsigned int *count,
                            unsigned int start, unsigned int end)
{
  *regions = (region_t *)ck_realloc(*regions, (*count + 1U) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

/* POP3 commands are CRLF-terminated single-line records. Keep malformed LF
   records and a truncated final command visible to the mutator as well. */
region_t *extract_requests_pop3(unsigned char *buf, unsigned int buf_size,
                                unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0;
  unsigned int start = 0;

  if (!region_count_ref) return NULL;
  if (!buf || !buf_size) {
    *region_count_ref = 0;
    return NULL;
  }
  if (buf_size > (unsigned int)INT_MAX) {
    pop3_add_region(&regions, &count, 0U, (unsigned int)INT_MAX - 1U);
    *region_count_ref = count;
    return regions;
  }

  for (unsigned int i = 0; i < buf_size; ++i) {
    if (buf[i] != '\n') continue;
    pop3_add_region(&regions, &count, start, i);
    start = i + 1U;
  }
  if (start < buf_size) pop3_add_region(&regions, &count, start, buf_size - 1U);
  *region_count_ref = count;
  return regions;
}

static unsigned int pop3_line_status(const unsigned char *line,
                                    unsigned int length)
{
  if (length >= 3U && line[0] == '+' &&
      (unsigned char)toupper(line[1]) == 'O' &&
      (unsigned char)toupper(line[2]) == 'K' &&
      (length == 3U || line[3] == ' ' || line[3] == '\t'))
    return 1U;
  if (length >= 4U && line[0] == '-' &&
      (unsigned char)toupper(line[1]) == 'E' &&
      (unsigned char)toupper(line[2]) == 'R' &&
      (unsigned char)toupper(line[3]) == 'R' &&
      (length == 4U || line[4] == ' ' || line[4] == '\t'))
    return 2U;
  return 0U;
}

static int pop3_starts_multiline(const unsigned char *line,
                                unsigned int length)
{
  static const char *const markers[] = {
      "list follows", "listing follows", "messages", "message", "octets"};
  for (unsigned int marker = 0; marker < sizeof(markers) / sizeof(markers[0]);
       ++marker) {
    unsigned int marker_length = (unsigned int)strlen(markers[marker]);
    if (marker_length > length) continue;
    for (unsigned int i = 0; i + marker_length <= length; ++i) {
      unsigned int j = 0;
      while (j < marker_length &&
             (unsigned char)tolower(line[i + j]) ==
                 (unsigned char)markers[marker][j])
        ++j;
      if (j == marker_length) return 1;
    }
  }
  return 0;
}

static void pop3_add_state(unsigned int **states, unsigned int *count,
                           unsigned int state)
{
  *states = (unsigned int *)ck_realloc(*states,
                                       (*count + 1U) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

/* POP3 is line-oriented, but positive multi-line responses carry arbitrary
   mailbox bytes. Count status lines and dot terminators; ignore message/body
   lines to avoid inventing state IDs from user-controlled payload text. */
unsigned int *extract_response_codes_pop3(unsigned char *buf,
                                          unsigned int buf_size,
                                          unsigned int *state_count_ref)
{
  unsigned int *states = NULL;
  unsigned int count = 0;
  unsigned int offset = 0;
  int in_multiline = 0;

  if (!state_count_ref) return NULL;
  pop3_add_state(&states, &count, 0U);
  if (!buf || !buf_size) {
    *state_count_ref = count;
    return states;
  }

  while (offset < buf_size) {
    unsigned int end = offset;
    unsigned int length;
    while (end < buf_size && buf[end] != '\n') ++end;
    if (end == buf_size) break;
    length = end - offset;
    if (length && buf[offset + length - 1U] == '\r') --length;

    if (in_multiline) {
      if (length == 1U && buf[offset] == '.') {
        pop3_add_state(&states, &count, 3U);
        in_multiline = 0;
      }
    } else {
      unsigned int status = pop3_line_status(buf + offset, length);
      if (status) {
        pop3_add_state(&states, &count, status);
        if (status == 1U && pop3_starts_multiline(buf + offset, length))
          in_multiline = 1;
      }
    }
    offset = end + 1U;
  }

  *state_count_ref = count;
  return states;
}
