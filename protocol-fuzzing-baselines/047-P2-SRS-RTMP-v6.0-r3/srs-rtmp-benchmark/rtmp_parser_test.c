#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include "types.h"
#include "alloc-inl.h"
#include "aflnet.h"

int main(void)
{
  unsigned char input[3073 + 1537 + 1536 + 1 + 11 + 130 + 1 + 2];
  unsigned char response[3073 + 1 + 11 + 6];
  unsigned char ordinary[1 + 11 + 6];
  unsigned int regions_count = 0, states_count = 0;
  region_t *regions;
  unsigned int *states;
  size_t pos = 0;

  memset(input, 0, sizeof(input));
  input[0] = 3;
  pos = 1537 + 1536;
  input[pos++] = 0x03;                 /* fmt=0, chunk stream id=3 */
  input[pos++] = 0; input[pos++] = 0; input[pos++] = 0;
  input[pos++] = 0; input[pos++] = 0; input[pos++] = 130;
  input[pos++] = 20;                   /* AMF0 command */
  input[pos++] = 0; input[pos++] = 0; input[pos++] = 0; input[pos++] = 0;
  memset(input + pos, 'A', 128); pos += 128;
  input[pos++] = 0xc3;                 /* fmt=3 continuation */
  input[pos++] = 'B'; input[pos++] = 'C';
  regions = extract_requests_rtmp(input, (unsigned int)pos, &regions_count);
  if (regions_count != 3 || regions[0].end_byte - regions[0].start_byte + 1 != 1537 ||
      regions[1].end_byte - regions[1].start_byte + 1 != 1536 ||
      regions[2].end_byte - regions[2].start_byte + 1 != 1 + 11 + 128 + 1 + 2) {
    fprintf(stderr, "RTMP request segmentation failed: regions=%u\n", regions_count);
    ck_free(regions);
    return 1;
  }
  ck_free(regions);

  memset(response, 0, sizeof(response));
  response[0] = 3;
  pos = 3073;
  response[pos++] = 0x03;
  response[pos++] = 0; response[pos++] = 0; response[pos++] = 0;
  response[pos++] = 0; response[pos++] = 0; response[pos++] = 6;
  response[pos++] = 20;
  response[pos++] = 0; response[pos++] = 0; response[pos++] = 0; response[pos++] = 0;
  response[pos++] = 2; response[pos++] = 0; response[pos++] = 3;
  response[pos++] = 'o'; response[pos++] = 'k'; response[pos++] = '!';
  states = extract_response_codes_rtmp(response, (unsigned int)pos, &states_count);
  if (states_count != 3 || states[0] != 0 || states[1] != 3 ||
      (states[2] >> 24) != 20) {
    fprintf(stderr, "RTMP response states failed: states=%u\n", states_count);
    ck_free(states);
    return 1;
  }
  ck_free(states);
  memcpy(ordinary, response + 3073, sizeof(ordinary));
  states = extract_response_codes_rtmp(ordinary, sizeof(ordinary), &states_count);
  if (states_count != 2 || states[0] != 0 || (states[1] >> 24) != 20) {
    fprintf(stderr, "RTMP non-handshake response beginning with 0x03 was misclassified.\n");
    ck_free(states);
    return 1;
  }
  ck_free(states);
  puts("RTMP handshake segmentation, chunk continuations, and AMF response states passed.");
  return 0;
}
