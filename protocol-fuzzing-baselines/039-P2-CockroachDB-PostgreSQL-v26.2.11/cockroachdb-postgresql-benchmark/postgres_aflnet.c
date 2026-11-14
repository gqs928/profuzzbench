/* PostgreSQL 前后端协议的 AFLNet 报文边界与状态解析器。 */
#include <limits.h>
#include <stdint.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

#define PG_STATE_INIT 0U
#define PG_STATE_AUTH_OK 1U
#define PG_STATE_AUTH_CHALLENGE 2U
#define PG_STATE_READY_IDLE 10U
#define PG_STATE_READY_TX 11U
#define PG_STATE_READY_FAILED_TX 12U
#define PG_STATE_COMMAND 20U
#define PG_STATE_ROW_DESCRIPTION 21U
#define PG_STATE_DATA_ROW 22U
#define PG_STATE_EXTENDED_COMPLETE 23U
#define PG_STATE_COPY 30U
#define PG_STATE_AUTH_ERROR 40U
#define PG_STATE_SQL_ERROR 41U
#define PG_STATE_NOTICE 50U
#define PG_STATE_PARAMETER 51U
#define PG_STATE_BACKEND_KEY 52U
#define PG_STATE_NEGOTIATION 53U
#define PG_STATE_SSL_REJECTED 54U
#define PG_STATE_OTHER 99U

static uint32_t pg_read_u32(const unsigned char *buf)
{
  return ((uint32_t)buf[0] << 24) | ((uint32_t)buf[1] << 16) |
         ((uint32_t)buf[2] << 8) | (uint32_t)buf[3];
}

static void pg_append_region(region_t **regions, unsigned int *count,
                             unsigned int start, unsigned int end)
{
  *regions = (region_t *)ck_realloc(*regions, (*count + 1U) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

/* 首包没有类型字节；SSL、GSS、Cancel 与 Startup 都使用长度开头。 */
static int pg_is_initial_packet(const unsigned char *buf, unsigned int size,
                                unsigned int *frame_size)
{
  uint32_t declared;

  if (!buf || size < 8U || buf[0] != 0) return 0;
  declared = pg_read_u32(buf);
  if (declared < 8U || declared > size || declared > (uint32_t)INT_MAX)
    return 0;
  *frame_size = declared;
  return 1;
}

/* 按 PostgreSQL 的消息长度字段切包，遇到畸形尾部时保留完整变异区。 */
static int pg_next_request(const unsigned char *buf, unsigned int size,
                           unsigned int *frame_size)
{
  uint32_t declared;

  if (!buf || !size || !frame_size) return 0;
  /* SSL/GSS 协商拒绝后的 StartupMessage 仍然没有类型字节。 */
  if (pg_is_initial_packet(buf, size, frame_size)) return 1;
  if (size < 5U) return 0;
  declared = pg_read_u32(buf + 1U);
  if (declared < 4U || declared > size - 1U ||
      declared >= (uint32_t)INT_MAX)
    return 0;
  *frame_size = declared + 1U;
  return 1;
}

region_t *extract_requests_postgres(unsigned char *buf, unsigned int buf_size,
                                    unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0, start = 0;

  if (!region_count_ref) return NULL;
  if (!buf || !buf_size) {
    *region_count_ref = 0;
    return NULL;
  }

  while (start < buf_size) {
    unsigned int frame_size = 0;
    if (!pg_next_request(buf + start, buf_size - start, &frame_size) ||
        !frame_size || frame_size > (unsigned int)INT_MAX ||
        start > (unsigned int)INT_MAX - frame_size) {
      pg_append_region(&regions, &count, start, buf_size - 1U);
      break;
    }
    pg_append_region(&regions, &count, start, start + frame_size - 1U);
    start += frame_size;
  }
  *region_count_ref = count;
  return regions;
}

/* 读取 ErrorResponse 的 SQLSTATE，字段顺序按协议允许的方式扫描。 */
static int pg_error_sqlstate(const unsigned char *frame, unsigned int size,
                             char sqlstate[6])
{
  unsigned int pos = 5U;

  if (!frame || size < 6U || frame[0] != 'E') return 0;
  while (pos < size && frame[pos] != 0) {
    unsigned char field = frame[pos++];
    unsigned int start = pos;
    while (pos < size && frame[pos] != 0) pos++;
    if (pos >= size) return 0;
    if (field == 'C' && pos - start == 5U) {
      memcpy(sqlstate, frame + start, 5U);
      sqlstate[5] = '\0';
      return 1;
    }
    pos++;
  }
  return 0;
}

static unsigned int pg_response_state(const unsigned char *frame,
                                      unsigned int frame_size)
{
  unsigned char type;
  uint32_t declared;
  char sqlstate[6];

  if (!frame || !frame_size) return PG_STATE_OTHER;
  if (frame_size == 1U && frame[0] == 'N')
    return PG_STATE_SSL_REJECTED;
  if (frame_size < 5U) return PG_STATE_OTHER;

  type = frame[0];
  declared = pg_read_u32(frame + 1U);
  if (declared < 4U || declared + 1U != frame_size)
    return PG_STATE_OTHER;

  switch (type) {
    case 'R':
      if (declared < 8U) return PG_STATE_OTHER;
      if (pg_read_u32(frame + 5U) == 0U) return PG_STATE_AUTH_OK;
      return PG_STATE_AUTH_CHALLENGE;
    case 'Z':
      if (declared != 5U) return PG_STATE_OTHER;
      if (frame[5] == 'I') return PG_STATE_READY_IDLE;
      if (frame[5] == 'T') return PG_STATE_READY_TX;
      if (frame[5] == 'E') return PG_STATE_READY_FAILED_TX;
      return PG_STATE_OTHER;
    case 'C': case 'I':
      return PG_STATE_COMMAND;
    case 'T':
      return PG_STATE_ROW_DESCRIPTION;
    case 'D':
      return PG_STATE_DATA_ROW;
    case '1': case '2': case '3': case 'n': case 's':
      return PG_STATE_EXTENDED_COMPLETE;
    case 'G': case 'H': case 'W': case 'd': case 'c': case 'f':
      return PG_STATE_COPY;
    case 'E':
      if (pg_error_sqlstate(frame, frame_size, sqlstate) &&
          sqlstate[0] == '2' && sqlstate[1] == '8')
        return PG_STATE_AUTH_ERROR;
      return PG_STATE_SQL_ERROR;
    case 'N': case 'A':
      return PG_STATE_NOTICE;
    case 'S':
      return PG_STATE_PARAMETER;
    case 'K':
      return PG_STATE_BACKEND_KEY;
    case 'v':
      return PG_STATE_NEGOTIATION;
    default:
      return PG_STATE_OTHER;
  }
}

/* 后端消息都有类型字节；SSL/GSS 协商拒绝是单字节响应。 */
static int pg_next_response(const unsigned char *buf, unsigned int size,
                            unsigned int *frame_size)
{
  uint32_t declared;

  if (!buf || !size || !frame_size) return 0;
  if (buf[0] == 'N' && (size == 1U || buf[1] != 0)) {
    *frame_size = 1U;
    return 1;
  }
  if (size < 5U) return 0;
  declared = pg_read_u32(buf + 1U);
  if (declared < 4U || declared > size - 1U ||
      declared >= (uint32_t)INT_MAX)
    return 0;
  *frame_size = declared + 1U;
  return 1;
}

unsigned int *extract_response_codes_postgres(unsigned char *buf,
                                              unsigned int buf_size,
                                              unsigned int *state_count_ref)
{
  unsigned int *states, count = 1U, cursor = 0U;

  if (!state_count_ref) return NULL;
  states = (unsigned int *)ck_alloc(sizeof(unsigned int));
  states[0] = PG_STATE_INIT;
  if (!buf || !buf_size) {
    *state_count_ref = count;
    return states;
  }

  while (cursor < buf_size) {
    unsigned int frame_size = 0;
    if (!pg_next_response(buf + cursor, buf_size - cursor, &frame_size) ||
        !frame_size)
      break;
    states = (unsigned int *)ck_realloc(
        states, (count + 1U) * sizeof(unsigned int));
    states[count++] = pg_response_state(buf + cursor, frame_size);
    cursor += frame_size;
  }
  *state_count_ref = count;
  return states;
}
