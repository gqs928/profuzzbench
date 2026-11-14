/* Unit check for MongoDB message framing and OP_MSG response-state classes. */
#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static void write_u32le(unsigned char *buf, uint32_t value)
{
  buf[0] = (unsigned char)value;
  buf[1] = (unsigned char)(value >> 8);
  buf[2] = (unsigned char)(value >> 16);
  buf[3] = (unsigned char)(value >> 24);
}

static unsigned int make_ok_response(unsigned char *buf, unsigned int request_id)
{
  static const unsigned char bson_ok[] = {
      17, 0, 0, 0, 0x01, 'o', 'k', 0,
      0, 0, 0, 0, 0, 0, 0xf0, 0x3f, 0};
  unsigned int length = 16U + 4U + 1U + sizeof(bson_ok);
  memset(buf, 0, length);
  write_u32le(buf, length);
  write_u32le(buf + 4, 100U);
  write_u32le(buf + 8, request_id);
  write_u32le(buf + 12, 2013U);
  buf[20] = 0U;
  memcpy(buf + 21, bson_ok, sizeof(bson_ok));
  return length;
}

static unsigned int make_error_response(unsigned char *buf, unsigned int request_id)
{
  static const unsigned char bson_error[] = {
      27, 0, 0, 0,
      0x01, 'o', 'k', 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0x10, 'c', 'o', 'd', 'e', 0, 42, 0, 0, 0,
      0};
  unsigned int length = 16U + 4U + 1U + sizeof(bson_error);
  memset(buf, 0, length);
  write_u32le(buf, length);
  write_u32le(buf + 4, 101U);
  write_u32le(buf + 8, request_id);
  write_u32le(buf + 12, 2013U);
  buf[20] = 0U;
  memcpy(buf + 21, bson_error, sizeof(bson_error));
  return length;
}

int main(void)
{
  unsigned char requests[40] = {0};
  unsigned char responses[128] = {0};
  unsigned int region_count = 0U;
  unsigned int state_count = 0U;
  region_t *regions;
  unsigned int *states;
  unsigned int response_size;

  write_u32le(requests, 16U);
  write_u32le(requests + 16U, 16U);
  write_u32le(requests + 32U, 32U); /* truncated trailing message */
  regions = extract_requests_mongodb(requests, sizeof(requests), &region_count);
  assert(region_count == 3U);
  assert(regions[0].start_byte == 0 && regions[0].end_byte == 15);
  assert(regions[1].start_byte == 16 && regions[1].end_byte == 31);
  assert(regions[2].start_byte == 32 && regions[2].end_byte == 39);
  ck_free(regions);

  response_size = make_ok_response(responses, 1U);
  response_size += make_error_response(responses + response_size, 2U);
  states = extract_response_codes_mongodb(responses, response_size, &state_count);
  assert(state_count == 3U);
  assert(states[0] == 0U && states[1] == 1U && states[2] == 0x1002aU);
  ck_free(states);
  return 0;
}
