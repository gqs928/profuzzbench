#include <stdio.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

int main(void)
{
  unsigned char request[] = "CAPABILITIES\r\nMODE READER\r\nGROUP comp.test\r\nDATE";
  unsigned char response[] =
    "200 nntp.test ready\r\n"
    "101 Capability list:\r\nVERSION 2\r\nREADER\r\n.\r\n"
    "211 2 1 2 comp.test\r\n"
    "111 20261108010203\r\n";
  const unsigned int expected[] = {0, 1200, 1101, 2000, 1211, 1111};
  const char *parts[] = {"CAPABILITIES\r\n", "MODE READER\r\n",
                         "GROUP comp.test\r\n", "DATE"};
  unsigned int req_count = 0, state_count = 0, i, offset = 0;
  region_t *regions = extract_requests_nntp(request, sizeof(request) - 1,
                                           &req_count);
  unsigned int *states = extract_response_codes_nntp(response,
                                                      sizeof(response) - 1,
                                                      &state_count);
  if (req_count != 4 || state_count != sizeof(expected) / sizeof(expected[0])) {
    fprintf(stderr, "NNTP parser count mismatch: requests=%u states=%u\n",
            req_count, state_count);
    return 1;
  }
  for (i = 0; i < req_count; i++) {
    unsigned int length = (unsigned int)strlen(parts[i]);
    if (regions[i].start_byte != (int)offset ||
        regions[i].end_byte != (int)(offset + length - 1) ||
        memcmp(request + offset, parts[i], length)) {
      fprintf(stderr, "NNTP request boundary mismatch at %u\n", i);
      return 1;
    }
    offset += length;
  }
  for (i = 0; i < state_count; i++) {
    if (states[i] != expected[i]) {
      fprintf(stderr, "NNTP state mismatch at %u: got %u expected %u\n",
              i, states[i], expected[i]);
      return 1;
    }
  }
  ck_free(regions);
  ck_free(states);
  puts("PASS: CRLF commands, numeric reply states, and dot-terminated replies.");
  return 0;
}
