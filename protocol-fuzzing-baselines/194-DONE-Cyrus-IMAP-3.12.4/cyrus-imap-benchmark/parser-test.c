#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

region_t *extract_requests_imap(unsigned char *, unsigned int, unsigned int *);
unsigned int *extract_response_codes_imap(unsigned char *, unsigned int, unsigned int *);

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
      "A1 NOOP\r\nB1 LOGIN fuzzuser \"quoted\\\" value\"\r\n";
  unsigned char literal[] =
      "A2 APPEND INBOX {7+}\r\na\r\nb{x}\r\nA3 LOGOUT\r\n";
  unsigned char truncated[] = "A4 APPEND INBOX {9+}\r\nabc";
  unsigned char responses[] =
      "* OK ready\r\n* 2 EXISTS\r\nA1 OK complete\r\n+ continue\r\n";
  region_t *regions;
  unsigned int *states;
  unsigned int count = 0;
  unsigned int states_count = 0;

  regions = extract_requests_imap(commands, sizeof(commands) - 1U, &count);
  require(count == 2U, "two line commands split into two requests");
  require(regions[0].start_byte == 0 && regions[0].end_byte == 8,
          "first command includes CRLF");
  require(regions[1].start_byte == 9 && regions[1].end_byte == sizeof(commands) - 2U,
          "quoted command stays intact");
  ck_free(regions);

  regions = extract_requests_imap(literal, sizeof(literal) - 1U, &count);
  require(count == 2U, "literal payload CRLF does not split APPEND");
  require(regions[0].end_byte == (int)(strstr((char *)literal, "A3 LOGOUT") - (char *)literal) - 1,
          "APPEND region includes literal payload and terminating CRLF");
  ck_free(regions);

  regions = extract_requests_imap(truncated, sizeof(truncated) - 1U, &count);
  require(count == 1U && regions[0].start_byte == 0,
          "truncated literal is preserved as one tail region");
  ck_free(regions);

  states = extract_response_codes_imap(responses, sizeof(responses) - 1U,
                                       &states_count);
  require(states_count == 5U, "response parser includes sentinel and four lines");
  require(states[0] == 0U && states[1] == 1U && states[2] >= 100U &&
          states[3] == 10U && states[4] == 20U,
          "response classes separate greeting, untagged, tagged, continuation");
  ck_free(states);

  puts("PASS: IMAP command, literal, truncation and response-state parser checks");
  return 0;
}
