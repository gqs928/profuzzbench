/* MySQL/MariaDB/TiDB classic packet framing and response-state adapter for AFLNet. */
#include <limits.h>
#include <stdint.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

enum {
  MYSQL_STATE_GREETING = 1,
  MYSQL_STATE_AUTH_OK = 10,
  MYSQL_STATE_AUTH_ERROR = 11,
  MYSQL_STATE_AUTH_MORE = 12,
  MYSQL_STATE_AUTH_SWITCH = 13,
  MYSQL_STATE_RESULT_HEADER = 20,
  MYSQL_STATE_ROW_OR_COLUMN = 21,
  MYSQL_STATE_EOF = 22,
  MYSQL_STATE_OK = 30,
  MYSQL_STATE_SQL_ERROR = 40,
  MYSQL_STATE_LOCAL_INFILE = 41,
  MYSQL_STATE_OTHER = 99
};

static uint32_t mysql_le24(const unsigned char *p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16);
}

static void mysql_append_region(region_t **regions, unsigned int *count,
                                unsigned int start, unsigned int end) {
  *regions = (region_t *)ck_realloc(*regions, (*count + 1U) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

region_t *extract_requests_mysql(unsigned char *buf, unsigned int buf_size,
                                 unsigned int *region_count_ref) {
  region_t *regions = NULL;
  unsigned int count = 0, start = 0;
  if (!region_count_ref) return NULL;
  if (!buf || !buf_size) { *region_count_ref = 0; return NULL; }
  while (start < buf_size) {
    unsigned int remain = buf_size - start;
    if (remain < 4U) {
      mysql_append_region(&regions, &count, start, buf_size - 1U);
      break;
    }
    uint32_t payload_len = mysql_le24(buf + start);
    if (payload_len > remain - 4U ||
        payload_len > (uint32_t)INT_MAX - 4U ||
        start > (unsigned int)INT_MAX - payload_len - 4U) {
      mysql_append_region(&regions, &count, start, buf_size - 1U);
      break;
    }
    unsigned int frame_len = payload_len + 4U;
    mysql_append_region(&regions, &count, start, start + frame_len - 1U);
    start += frame_len;
  }
  *region_count_ref = count;
  return regions;
}

static unsigned int mysql_classify_packet(const unsigned char *p, uint32_t n) {
  if (!n) return MYSQL_STATE_OTHER;
  switch (p[0]) {
    case 0x00:
      /* A classic-protocol OK payload is at least 7 bytes; shorter 0x00-leading
         payloads can be result rows containing empty length-encoded fields. */
      return n >= 7U ? MYSQL_STATE_OK : MYSQL_STATE_ROW_OR_COLUMN;
    case 0xff:
      return MYSQL_STATE_SQL_ERROR;
    case 0xfe:
      return n < 9U ? MYSQL_STATE_EOF : MYSQL_STATE_ROW_OR_COLUMN;
    case 0xfb:
      return MYSQL_STATE_LOCAL_INFILE;
    default:
      /* The proxy consumes greeting/auth rounds; remaining 0x01 and length-encoded
         payload markers belong to ordinary SQL result packets. */
      return (p[0] > 0 && p[0] < 0xfb) ? MYSQL_STATE_ROW_OR_COLUMN : MYSQL_STATE_OTHER;
  }
}

unsigned int *extract_response_codes_mysql(unsigned char *buf,
                                           unsigned int buf_size,
                                           unsigned int *state_count_ref) {
  unsigned int *states = NULL, count = 0, start = 0;
  if (!state_count_ref) return NULL;
  if (!buf || !buf_size) { *state_count_ref = 0; return NULL; }
  while (start < buf_size) {
    unsigned int remain = buf_size - start;
    if (remain < 4U) break;
    uint32_t payload_len = mysql_le24(buf + start);
    if (payload_len > remain - 4U) break;
    unsigned int state = mysql_classify_packet(buf + start + 4U, payload_len);
    states = (unsigned int *)ck_realloc(states, (count + 1U) * sizeof(unsigned int));
    states[count++] = state;
    start += payload_len + 4U;
  }
  /* The auth proxy consumes greeting/auth packets, so the first response
     visible to AFLNet has no observed pre-auth state. Add AFLNet's canonical
     initial state 0 so state-aware initialization can link it to the first
     SQL response state instead of treating the first SQL state as a root. */
  if (count) {
    states = (unsigned int *)ck_realloc(states, (count + 1U) * sizeof(unsigned int));
    memmove(states + 1U, states, count * sizeof(unsigned int));
    states[0] = 0U;
    count++;
  }
  *state_count_ref = count;
  return states;
}
