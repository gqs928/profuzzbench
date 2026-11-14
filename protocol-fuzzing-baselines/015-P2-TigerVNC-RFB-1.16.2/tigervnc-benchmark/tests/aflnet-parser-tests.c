#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "types.h"
#include "alloc-inl.h"
#include "aflnet.h"

static void free_regions(region_t *regions, unsigned int count) {
  unsigned int i;
  for (i = 0; i < count; i++) ck_free(regions[i].state_sequence);
  ck_free(regions);
}

static void test_rfb_client_regions(void) {
  unsigned char request[] = {
    'R','F','B',' ','0','0','3','.','0','0','8','\n',
    1, 1,
    3, 0, 0, 0, 0, 0, 2, 0x80, 1, 0xe0,
    4, 1, 0, 0, 0, 0, 0, 0x41
  };
  unsigned int count = 0;
  region_t *regions = extract_requests_rfb(request, sizeof(request), &count);
  assert(count == 5);
  assert(regions[0].start_byte == 0 && regions[0].end_byte == 11);
  assert(regions[1].start_byte == 12 && regions[1].end_byte == 12);
  assert(regions[2].start_byte == 13 && regions[2].end_byte == 13);
  assert(regions[3].start_byte == 14 && regions[3].end_byte == 23);
  assert(regions[4].start_byte == 24 && regions[4].end_byte == 31);
  free_regions(regions, count);
}

static void test_rfb_server_states(void) {
  unsigned char response[] = {
    'R','F','B',' ','0','0','3','.','0','0','8','\n',
    1, 1, 0, 0, 0, 0,
    0x02,0x80,0x01,0xe0,
    32,24,0,1, 0,255,0,255,0,255, 0,8,16, 0,0,0,
    0,0,0,4, 't','e','s','t'
  };
  unsigned int count = 0;
  unsigned int *states = extract_response_codes_rfb(response, sizeof(response), &count);
  assert(count == 5);
  assert(states[1] == 0x10000308U);
  assert(states[2] == 0x20000001U);
  assert(states[3] == 0x30000000U);
  assert(states[4] == 0x40000001U);
  ck_free(states);
}

static void test_rfb_oversized_text_guard(void) {
  unsigned char request[] = {6, 0, 0, 0, 0xff, 0xff, 0xff, 0xff};
  unsigned int count = 0;
  region_t *regions = extract_requests_rfb(request, sizeof(request), &count);
  assert(count == 1 && regions[0].start_byte == 0 && regions[0].end_byte == 7);
  free_regions(regions, count);
}

static void test_rdp_tpkt_and_negotiation_state(void) {
  unsigned char request[] = {
    3,0,0,19, 14,0xe0,0,0,0,0,0,1,0,8,0,3,0,0,0
  };
  unsigned char response[] = {
    3,0,0,19, 14,0xd0,0,0,0,0,0,2,0,0,8,0,0,0,0
  };
  unsigned int count = 0;
  region_t *regions = extract_requests_rdp(request, sizeof(request), &count);
  assert(count == 1 && regions[0].start_byte == 0 && regions[0].end_byte == 18);
  free_regions(regions, count);
  count = 0;
  unsigned int *states = extract_response_codes_rdp(response, sizeof(response), &count);
  assert(count == 2 && states[1] == 0x20000000U);
  ck_free(states);
}

static void test_rdp_malformed_tpkt_guard(void) {
  unsigned char request[] = {3,0,0,3};
  unsigned int count = 0;
  region_t *regions = extract_requests_rdp(request, sizeof(request), &count);
  assert(count == 1 && regions[0].start_byte == 0 && regions[0].end_byte == 3);
  free_regions(regions, count);
}

int main(void) {
  test_rfb_client_regions();
  test_rfb_server_states();
  test_rfb_oversized_text_guard();
  test_rdp_tpkt_and_negotiation_state();
  test_rdp_malformed_tpkt_guard();
  puts("RFB/RDP parser tests passed");
  return 0;
}
