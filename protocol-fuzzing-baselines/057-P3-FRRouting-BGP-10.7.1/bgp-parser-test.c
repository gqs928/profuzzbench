#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct region {
  int start_byte;
  int end_byte;
  int modifiable;
  unsigned int *state_sequence;
  unsigned int state_count;
} region_t;

#define ck_realloc(ptr, size) realloc((ptr), (size))
#include "bgp_aflnet.inc"

static void test_request_framing(void) {
  unsigned char stream[41] = {0};
  unsigned int count = 0;
  region_t *regions;
  for (unsigned int i = 0; i < 16; ++i) stream[i] = 0xff;
  stream[16] = 0;
  stream[17] = 19;
  stream[18] = 4;
  for (unsigned int i = 19; i < 35; ++i) stream[i] = 0xff;
  stream[35] = 0;
  stream[36] = 5;
  stream[37] = 4;
  stream[38] = 0xff;
  stream[39] = 0xff;
  stream[40] = 0xff;
  regions = extract_requests_bgp(stream, (unsigned int)sizeof(stream), &count);
  assert(count == 2U);
  assert(regions[0].start_byte == 0 && regions[0].end_byte == 18);
  assert(regions[1].start_byte == 19 && regions[1].end_byte == 40);
  free(regions);
}

static void test_response_states(void) {
  unsigned char response[40] = {0};
  unsigned int count = 0;
  unsigned int *states;
  for (unsigned int i = 0; i < 16; ++i) response[i] = 0xff;
  response[17] = 19;
  response[18] = 4;
  for (unsigned int i = 19; i < 35; ++i) response[i] = 0xff;
  response[36] = 21;
  response[37] = 3;
  response[38] = 2;
  response[39] = 3;
  states = extract_response_codes_bgp(response, (unsigned int)sizeof(response), &count);
  assert(count == 3U);
  assert(states[0] == 0U);
  assert(states[1] == 0xB10004U);
  assert(states[2] == 0xB30203U);
  free(states);
}

static void test_truncated_message(void) {
  unsigned char response[19] = {0};
  unsigned int count = 0;
  unsigned int *states;
  response[17] = 20;
  response[18] = 1;
  states = extract_response_codes_bgp(response, (unsigned int)sizeof(response), &count);
  assert(count == 2U && states[1] == 0xB1FFFFU);
  free(states);
}

int main(void) {
  test_request_framing();
  test_response_states();
  test_truncated_message();
  puts("PASS: BGP multi-message framing, type/notification state, and truncation");
  return 0;
}
