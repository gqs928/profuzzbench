/* Kafka 协议适配：按四字节长度切请求帧，并用响应 correlation id 反馈阶段。 */
#include <limits.h>
#include <stdint.h>

#include "alloc-inl.h"
#include "aflnet.h"

enum {
  KAFKA_STATE_INIT = 0U,
  KAFKA_STATE_API_VERSIONS = 1U,
  KAFKA_STATE_METADATA = 2U,
  KAFKA_STATE_PRODUCE = 3U,
  KAFKA_STATE_FETCH = 4U,
  KAFKA_STATE_LIST_OFFSETS = 5U,
  KAFKA_STATE_FIND_COORDINATOR = 6U,
  KAFKA_STATE_OTHER = 99U
};

static uint32_t kafka_u32(const unsigned char *buf)
{
  return ((uint32_t)buf[0] << 24) | ((uint32_t)buf[1] << 16) |
         ((uint32_t)buf[2] << 8) | (uint32_t)buf[3];
}

static void kafka_append_region(region_t **regions, unsigned int *count,
                                unsigned int start, unsigned int end)
{
  *regions = (region_t *)ck_realloc(*regions, (*count + 1U) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1U;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0U;
  (*count)++;
}

/* Kafka 的帧长度不包含长度字段本身；异常尾部完整保留供模糊器变异。 */
region_t *extract_requests_kafka(unsigned char *buf, unsigned int buf_size,
                                 unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0U;
  unsigned int cursor = 0U;

  if (!region_count_ref) return NULL;
  if (!buf || !buf_size) {
    *region_count_ref = 0U;
    return NULL;
  }

  while (cursor < buf_size) {
    unsigned int remaining = buf_size - cursor;
    uint32_t declared;
    uint64_t frame_size;

    if (remaining < 4U) {
      kafka_append_region(&regions, &count, cursor, buf_size - 1U);
      break;
    }
    declared = kafka_u32(buf + cursor);
    frame_size = (uint64_t)declared + 4U;
    if (declared < 8U || frame_size > remaining || frame_size > (uint64_t)INT_MAX ||
        cursor > (unsigned int)INT_MAX - (unsigned int)frame_size) {
      kafka_append_region(&regions, &count, cursor, buf_size - 1U);
      break;
    }
    kafka_append_region(&regions, &count, cursor,
                        cursor + (unsigned int)frame_size - 1U);
    cursor += (unsigned int)frame_size;
  }

  *region_count_ref = count;
  return regions;
}

/* 固定种子把请求 API 阶段编码在 correlation id 中，响应原样回传该字段。 */
static unsigned int kafka_response_state(uint32_t correlation_id)
{
  switch (correlation_id) {
    case KAFKA_STATE_API_VERSIONS: return KAFKA_STATE_API_VERSIONS;
    case KAFKA_STATE_METADATA: return KAFKA_STATE_METADATA;
    case KAFKA_STATE_PRODUCE: return KAFKA_STATE_PRODUCE;
    case KAFKA_STATE_FETCH: return KAFKA_STATE_FETCH;
    case KAFKA_STATE_LIST_OFFSETS: return KAFKA_STATE_LIST_OFFSETS;
    case KAFKA_STATE_FIND_COORDINATOR: return KAFKA_STATE_FIND_COORDINATOR;
    default: return KAFKA_STATE_OTHER;
  }
}

/* 响应头至少包含长度和 correlation id；不完整尾部不伪造状态。 */
unsigned int *extract_response_codes_kafka(unsigned char *buf,
                                           unsigned int buf_size,
                                           unsigned int *state_count_ref)
{
  unsigned int *states;
  unsigned int count = 1U;
  unsigned int cursor = 0U;

  if (!state_count_ref) return NULL;
  states = (unsigned int *)ck_alloc(sizeof(unsigned int));
  states[0] = KAFKA_STATE_INIT;
  if (!buf || !buf_size) {
    *state_count_ref = count;
    return states;
  }

  while (buf_size - cursor >= 8U) {
    uint32_t declared = kafka_u32(buf + cursor);
    uint64_t frame_size = (uint64_t)declared + 4U;
    uint32_t correlation_id;

    if (declared < 4U || frame_size > buf_size - cursor || frame_size > INT_MAX)
      break;
    correlation_id = kafka_u32(buf + cursor + 4U);
    states = (unsigned int *)ck_realloc(states, (count + 1U) * sizeof(unsigned int));
    states[count++] = kafka_response_state(correlation_id);
    cursor += (unsigned int)frame_size;
  }

  *state_count_ref = count;
  return states;
}
