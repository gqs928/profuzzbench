/* 独立检查 Kafka 帧切分、畸形尾部保留和响应状态映射。 */
#include <assert.h>

#include "alloc-inl.h"
#include "aflnet.h"

static void free_regions(region_t *regions)
{
  ck_free(regions);
}

int main(void)
{
  unsigned char requests[] = {
      0, 0, 0, 8, 0, 18, 0, 0, 0, 1, 0, 0,
      0, 0, 0, 8, 0, 3, 0, 1, 0, 0, 0, 2,
      0, 0, 0, 3, 0xaa, 0xbb, 0xcc};
  unsigned char responses[] = {
      0, 0, 0, 8, 0, 0, 0, 1, 0, 0, 0, 0,
      0, 0, 0, 8, 0, 0, 0, 2, 0, 0, 0, 0,
      0, 0, 0, 8, 0, 0, 0, 4, 0, 0, 0, 0};
  unsigned int count = 0U;
  unsigned int state_count = 0U;
  region_t *regions = extract_requests_kafka(requests, sizeof(requests), &count);
  unsigned int *states = extract_response_codes_kafka(responses, sizeof(responses),
                                                       &state_count);

  assert(count == 3U);
  assert(regions[0].start_byte == 0 && regions[0].end_byte == 11);
  assert(regions[1].start_byte == 12 && regions[1].end_byte == 23);
  assert(regions[2].start_byte == 24 && regions[2].end_byte == 30);
  assert(state_count == 4U);
  assert(states[0] == 0U && states[1] == 1U && states[2] == 2U && states[3] == 4U);
  free_regions(regions);
  ck_free(states);

  {
    unsigned char truncated[] = {0, 0, 0, 40, 0, 3, 0, 1, 0xaa};
    regions = extract_requests_kafka(truncated, sizeof(truncated), &count);
    assert(count == 1U && regions[0].start_byte == 0 && regions[0].end_byte == 8);
    free_regions(regions);
  }
  return 0;
}
