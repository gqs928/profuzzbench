#include <stdio.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

int main(void)
{
  unsigned char request[] =
    "NICK fuzz\r\nUSER fuzz 0 * :Fuzz User\r\nJOIN #bench\r\nWHO #bench";
  unsigned char response[] =
    "@time=now :irc.test 001 fuzz :Welcome\r\n"
    ":irc.test 004 fuzz irc.test InspIRCd io\r\n"
    ":fuzz!u@127.0.0.1 JOIN #bench\r\n"
    ":irc.test 366 fuzz #bench :End of NAMES list\r\n"
    ":irc.test PING :incomplete-fragment";
  const unsigned int expected[] = {0, 1001, 1004, 2003, 1366};
  const char *parts[] = {"NICK fuzz\r\n", "USER fuzz 0 * :Fuzz User\r\n",
                         "JOIN #bench\r\n", "WHO #bench"};
  unsigned int regions_count = 0, states_count = 0, i;
  region_t *regions = extract_requests_irc(request, sizeof(request) - 1,
                                           &regions_count);
  unsigned int *states = extract_response_codes_irc(response,
                                                    sizeof(response) - 1,
                                                    &states_count);
  unsigned int offset = 0;

  if (regions_count != 4 || states_count != sizeof(expected) / sizeof(expected[0])) {
    fprintf(stderr, "IRC parser count mismatch: regions=%u states=%u\n",
            regions_count, states_count);
    return 1;
  }
  for (i = 0; i < regions_count; i++) {
    unsigned int length = (unsigned int)strlen(parts[i]);
    if (regions[i].start_byte != (int)offset ||
        regions[i].end_byte != (int)(offset + length - 1) ||
        memcmp(request + offset, parts[i], length)) {
      fprintf(stderr, "IRC request boundary mismatch at region %u\n", i);
      return 1;
    }
    offset += length;
  }
  for (i = 0; i < states_count; i++) {
    if (states[i] != expected[i]) {
      fprintf(stderr, "IRC state mismatch at %u: got %u expected %u\n",
              i, states[i], expected[i]);
      return 1;
    }
  }

  ck_free(regions);
  ck_free(states);
  puts("PASS: IRC requests split on CRLF; numeric and JOIN replies map to stable states.");
  return 0;
}
