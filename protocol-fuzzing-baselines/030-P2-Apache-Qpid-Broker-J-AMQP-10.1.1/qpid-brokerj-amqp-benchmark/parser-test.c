#include <stdio.h>
#include "alloc-inl.h"
#include "aflnet.h"

static int fail(const char *message)
{
  fprintf(stderr, "FAIL: %s\n", message);
  return 1;
}

int main(void)
{
  unsigned char request[] = {
    'A','M','Q','P',0,1,0,0,
    0,0,0,14,2,0,0,0,0,0x53,0x10,0xC0,1,0,
    0,0,0
  };
  unsigned char response[] = {
    'A','M','Q','P',0,0,0,0,
    0,0,0,14,2,0,0,0,0,0x53,0x10,0xC0,1,0,
    0,0,0,14,2,1,0,0,0,0x53,0x44,0xC0,1,0
  };
  const unsigned int expected[] = {0, 5000, 5016, 6068};
  unsigned int request_count = 0, state_count = 0, i;
  region_t *regions = extract_requests_amqp(request, sizeof(request), &request_count);
  unsigned int *states = extract_response_codes_amqp(response, sizeof(response),
                                                       &state_count);
  if (!regions || request_count != 3) return fail("header/frame/trailing-byte segmentation");
  if (regions[0].start_byte != 0 || regions[0].end_byte != 7 ||
      regions[1].start_byte != 8 || regions[1].end_byte != 21 ||
      regions[2].start_byte != 22 || regions[2].end_byte != 24)
    return fail("AMQP request frame bounds");
  if (!states || state_count != sizeof(expected) / sizeof(expected[0]))
    return fail("AMQP response-state count");
  for (i = 0; i < state_count; i++)
    if (states[i] != expected[i]) return fail("stable AMQP response states");
  ck_free(regions);
  ck_free(states);
  puts("PASS: AMQP protocol header, binary frame boundaries, and performative-state mapping.");
  return 0;
}
