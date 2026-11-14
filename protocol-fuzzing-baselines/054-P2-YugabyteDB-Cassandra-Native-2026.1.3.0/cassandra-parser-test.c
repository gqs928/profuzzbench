#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "aflnet.h"
#include "alloc-inl.h"
#include "cassandra_aflnet.inc"

int main(void) {
  unsigned char requests[] = {
      0x04, 0x00, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00,
      0x04, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x03, 0x61, 0x62, 0x63};
  unsigned int region_count = 0;
  region_t *regions = extract_requests_cassandra(requests, sizeof(requests),
                                                  &region_count);
  assert(region_count == 2);
  assert(regions[0].start_byte == 0 && regions[0].end_byte == 8);
  assert(regions[1].start_byte == 9 && regions[1].end_byte == 20);
  assert(regions[0].modifiable == 1 && regions[1].modifiable == 1);
  ck_free(regions);

  unsigned char responses[] = {
      0x84, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x00,
      0x84, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x04,
      0x00, 0x00, 0x00, 0x0a};
  unsigned int state_count = 0;
  unsigned int *states = extract_response_codes_cassandra(
      responses, sizeof(responses), &state_count);
  assert(state_count == 3);
  assert(states[0] == 0 && states[1] == 0x06 && states[2] == 0x1000a);
  ck_free(states);

  unsigned char truncated[] = {0x04, 0, 0, 0, 0x07, 0, 0, 0, 8, 1, 2};
  regions = extract_requests_cassandra(truncated, sizeof(truncated),
                                       &region_count);
  assert(region_count == 1);
  assert(regions[0].start_byte == 0 && regions[0].end_byte == 10);
  ck_free(regions);

  states = extract_response_codes_cassandra(truncated, sizeof(truncated),
                                             &state_count);
  assert(state_count == 2 && states[0] == 0 && states[1] == 0x1ffffU);
  ck_free(states);

  puts("PASS: Cassandra Native Protocol v4/v5 frame and state parser");
  return 0;
}
