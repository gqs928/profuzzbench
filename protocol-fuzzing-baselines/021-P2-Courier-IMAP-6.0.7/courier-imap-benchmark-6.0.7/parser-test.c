#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>

#include "alloc-inl.h"
#include "aflnet.h"

region_t *extract_requests_pop3(unsigned char *, unsigned int, unsigned int *);
unsigned int *extract_response_codes_pop3(unsigned char *, unsigned int,
                                          unsigned int *);

static void require(int condition, const char *message)
{
  if (!condition) {
    fprintf(stderr, "FAIL: %s\n", message);
    exit(1);
  }
}

int main(void)
{
  unsigned char commands[] =
      "CAPA\r\nUSER fuzzuser\r\nPASS fuzzpass\r\nSTAT\r\nQUIT\r\n";
  unsigned char partial[] = "USER fuzzuser\r\nPASS";
  unsigned char responses[] =
      "+OK POP3 ready\r\n"
      "+OK Capability list follows\r\nUSER\r\nSASL PLAIN\r\n.\r\n"
      "+OK Unique-ID listing follows\r\n1 123\r\n.\r\n"
      "+OK password accepted\r\n"
      "-ERR bad command\r\n";
  region_t *regions;
  unsigned int *states;
  unsigned int count = 0;
  unsigned int state_count = 0;

  regions = extract_requests_pop3(commands, sizeof(commands) - 1U, &count);
  require(count == 5U, "one request region per CRLF-terminated command");
  require(regions[0].start_byte == 0 && regions[0].end_byte == 5,
          "request region retains its CRLF");
  require(regions[4].end_byte == sizeof(commands) - 2U,
          "last request region reaches end of transcript");
  ck_free(regions);

  regions = extract_requests_pop3(partial, sizeof(partial) - 1U, &count);
  require(count == 2U && regions[1].start_byte == 15U &&
              regions[1].end_byte == sizeof(partial) - 2U,
          "truncated final request remains fuzzable");
  ck_free(regions);

  states = extract_response_codes_pop3(responses, sizeof(responses) - 1U,
                                       &state_count);
  require(state_count == 8U, "state sequence includes sentinel, statuses and multiline ends");
  require(states[0] == 0U && states[1] == 1U && states[2] == 1U &&
              states[3] == 3U && states[4] == 1U && states[5] == 3U &&
              states[6] == 1U && states[7] == 2U,
          "greeting, CAPA/UIDL multiline replies, login success and error map stably");
  ck_free(states);

  puts("PASS: POP3 line framing, truncated tail, status responses and multiline body");
  return 0;
}
