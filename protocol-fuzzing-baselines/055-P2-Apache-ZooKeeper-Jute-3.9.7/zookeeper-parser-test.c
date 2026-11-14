#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
typedef uint8_t u8;
typedef uint32_t u32;
#include "aflnet.h"
#include "alloc-inl.h"
#include "zookeeper_aflnet.inc"

int main(void) {
  unsigned char requests[] = {
      0, 0, 0, 5, 1, 2, 3, 4, 5,
      0, 0, 0, 4, 6, 7, 8, 9};
  unsigned int region_count = 0;
  region_t *regions = extract_requests_zookeeper(requests, sizeof(requests),
                                                  &region_count);
  assert(region_count == 2);
  assert(regions[0].start_byte == 0 && regions[0].end_byte == 8);
  assert(regions[1].start_byte == 9 && regions[1].end_byte == 16);
  assert(regions[0].modifiable == 1 && regions[1].modifiable == 1);
  ck_free(regions);

  /* ConnectResponse (37-byte body), then a successful 16-byte ReplyHeader. */
  unsigned char responses[4 + 37 + 4 + 16] = {0};
  responses[3] = 37;
  responses[7] = 0;       /* protocolVersion */
  responses[11] = 0x27;   /* timeout 10000 */
  responses[12] = 0x10;
  responses[23] = 16;     /* passwd length */
  responses[4 + 37 + 3] = 16;
  unsigned int reply = 4 + 37 + 4;
  responses[reply + 3] = 1; /* xid */

  unsigned int state_count = 0;
  unsigned int *states = extract_response_codes_zookeeper(
      responses, sizeof(responses), &state_count);
  assert(state_count == 3);
  assert(states[0] == 0 && states[1] == 0x10000U && states[2] == 0x20000U);
  ck_free(states);

  unsigned char truncated[] = {0, 0, 0, 8, 1, 2};
  regions = extract_requests_zookeeper(truncated, sizeof(truncated),
                                       &region_count);
  assert(region_count == 1);
  assert(regions[0].start_byte == 0 && regions[0].end_byte == 5);
  ck_free(regions);
  states = extract_response_codes_zookeeper(truncated, sizeof(truncated),
                                             &state_count);
  assert(state_count == 2 && states[0] == 0 && states[1] == 0x1ffffU);
  ck_free(states);

  puts("PASS: ZooKeeper Jute framing and response-state parser");
  return 0;
}
