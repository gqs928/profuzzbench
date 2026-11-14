/* AFLNet adapter for Redis RESP2/RESP3 over plaintext TCP. */
#include <limits.h>
#include <stdint.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

#define RESP_MAX_DEPTH 64U
#define RESP_MAX_ITEMS 100000U

typedef struct {
  const unsigned char *buf;
  unsigned int size;
  unsigned int pos;
  unsigned int items;
} resp_cursor_t;

static int resp_line(resp_cursor_t *cursor, const unsigned char **line,
                     unsigned int *length)
{
  unsigned int i;
  for (i = cursor->pos; i + 1 < cursor->size; i++) {
    if (cursor->buf[i] == '\r' && cursor->buf[i + 1] == '\n') {
      *line = cursor->buf + cursor->pos;
      *length = i - cursor->pos;
      cursor->pos = i + 2;
      return 1;
    }
  }
  return 0;
}

static int resp_integer(const unsigned char *line, unsigned int length,
                        int64_t *value)
{
  unsigned int i = 0;
  int negative = 0;
  uint64_t number = 0, limit;

  if (!length) return 0;
  if (line[i] == '-') {
    negative = 1;
    if (++i == length) return 0;
  }
  limit = negative ? ((uint64_t)INT64_MAX + 1U) : (uint64_t)INT64_MAX;
  for (; i < length; i++) {
    unsigned int digit;
    if (line[i] < '0' || line[i] > '9') return 0;
    digit = (unsigned int)(line[i] - '0');
    if (number > (limit - digit) / 10U) return 0;
    number = number * 10U + digit;
  }
  if (negative) {
    *value = number == (uint64_t)INT64_MAX + 1U
                 ? INT64_MIN : -(int64_t)number;
  } else {
    *value = (int64_t)number;
  }
  return 1;
}

static int resp_parse_value(resp_cursor_t *cursor, unsigned int depth);

static int resp_parse_streamed_blob(resp_cursor_t *cursor)
{
  while (cursor->items++ < RESP_MAX_ITEMS) {
    const unsigned char *line;
    unsigned int line_length;
    int64_t chunk_length;

    if (cursor->pos >= cursor->size || cursor->buf[cursor->pos++] != ';' ||
        !resp_line(cursor, &line, &line_length) ||
        !resp_integer(line, line_length, &chunk_length) || chunk_length < 0 ||
        (uint64_t)chunk_length > cursor->size - cursor->pos)
      return 0;
    if (chunk_length == 0) return 1;
    cursor->pos += (unsigned int)chunk_length;
    if (cursor->size - cursor->pos < 2 || cursor->buf[cursor->pos] != '\r' ||
        cursor->buf[cursor->pos + 1] != '\n')
      return 0;
    cursor->pos += 2;
  }
  return 0;
}

static int resp_parse_streamed_aggregate(resp_cursor_t *cursor,
                                         unsigned int depth)
{
  while (cursor->items++ < RESP_MAX_ITEMS) {
    const unsigned char *line;
    unsigned int line_length;
    if (cursor->pos < cursor->size && cursor->buf[cursor->pos] == '.') {
      cursor->pos++;
      if (!resp_line(cursor, &line, &line_length) || line_length != 0)
        return 0;
      return 1;
    }
    if (!resp_parse_value(cursor, depth + 1U)) return 0;
  }
  return 0;
}

static int resp_parse_value(resp_cursor_t *cursor, unsigned int depth)
{
  const unsigned char *line;
  unsigned int line_length;
  unsigned char type;
  int64_t length;

  if (depth > RESP_MAX_DEPTH || cursor->pos >= cursor->size ||
      cursor->items++ >= RESP_MAX_ITEMS)
    return 0;
  type = cursor->buf[cursor->pos++];

  switch (type) {
    case '+': case '-': case ':': case ',': case '(':
      return resp_line(cursor, &line, &line_length);
    case '#':
      return resp_line(cursor, &line, &line_length) && line_length == 1 &&
             (line[0] == 't' || line[0] == 'f');
    case '_':
      return resp_line(cursor, &line, &line_length) && line_length == 0;
    case '$': case '!': case '=': {
      if (!resp_line(cursor, &line, &line_length)) return 0;
      if (line_length == 1 && line[0] == '?')
        return type == '$' && resp_parse_streamed_blob(cursor);
      if (!resp_integer(line, line_length, &length)) return 0;
      if (length == -1 && type == '$') return 1;
      if (length < 0 || (uint64_t)length > cursor->size - cursor->pos)
        return 0;
      cursor->pos += (unsigned int)length;
      if (cursor->size - cursor->pos < 2 || cursor->buf[cursor->pos] != '\r' ||
          cursor->buf[cursor->pos + 1] != '\n')
        return 0;
      cursor->pos += 2;
      return 1;
    }
    case '*': case '%': case '~': case '|': case '>': {
      uint64_t children, i;
      if (!resp_line(cursor, &line, &line_length)) return 0;
      if (line_length == 1 && line[0] == '?')
        return resp_parse_streamed_aggregate(cursor, depth);
      if (!resp_integer(line, line_length, &length)) return 0;
      if (length == -1 && type == '*') return 1;
      if (length < 0 || (uint64_t)length > RESP_MAX_ITEMS) return 0;
      children = (uint64_t)length;
      if (type == '%' || type == '|') {
        if (children > RESP_MAX_ITEMS / 2U) return 0;
        children *= 2U;
      }
      for (i = 0; i < children; i++)
        if (!resp_parse_value(cursor, depth + 1U)) return 0;
      return 1;
    }
    default:
      return 0;
  }
}

static int resp_parse_frame(const unsigned char *buf, unsigned int size,
                            unsigned int *frame_size)
{
  resp_cursor_t cursor;
  const unsigned char *line;
  unsigned char first;

  if (!buf || !size) return 0;
  first = buf[0];
  if (first != '+' && first != '-' && first != ':' && first != '$' &&
      first != '*' && first != '_' && first != '#' && first != ',' &&
      first != '(' && first != '!' && first != '=' && first != '%' &&
      first != '~' && first != '|' && first != '>') {
    /* Redis also accepts its legacy inline command format. */
    cursor.buf = buf;
    cursor.size = size;
    cursor.pos = 0;
    cursor.items = 0;
    if (!resp_line(&cursor, &line, frame_size)) return 0;
    return cursor.pos > 0;
  }

  cursor.buf = buf;
  cursor.size = size;
  cursor.pos = 0;
  cursor.items = 0;
  if (!resp_parse_value(&cursor, 0) || cursor.pos == 0) return 0;
  *frame_size = cursor.pos;
  return 1;
}

static void redis_append_region(region_t **regions, unsigned int *count,
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

region_t *extract_requests_redis(unsigned char *buf, unsigned int buf_size,
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
    if (!resp_parse_frame(buf + start, buf_size - start, &frame_size) ||
        !frame_size || frame_size > (unsigned int)INT_MAX ||
        start > (unsigned int)INT_MAX - frame_size) {
      redis_append_region(&regions, &count, start, buf_size - 1U);
      break;
    }
    redis_append_region(&regions, &count, start, start + frame_size - 1U);
    start += frame_size;
  }
  *region_count_ref = count;
  return regions;
}

static int resp_simple_payload_is(const unsigned char *frame,
                                  unsigned int frame_size,
                                  unsigned char type,
                                  const char *payload)
{
  unsigned int payload_length = (unsigned int)strlen(payload);
  unsigned int i;
  if (!frame || frame_size < payload_length + 3U || frame[0] != type)
    return 0;
  for (i = 0; i < payload_length; i++)
    if (frame[i + 1U] != (unsigned char)payload[i]) return 0;
  return frame[payload_length + 1U] == '\r' &&
         frame[payload_length + 2U] == '\n';
}

static int resp_error_has_code(const unsigned char *frame,
                               unsigned int frame_size,
                               const char *code)
{
  unsigned int length = (unsigned int)strlen(code), i;
  if (!frame || frame_size < length + 3U || frame[0] != '-') return 0;
  for (i = 0; i < length; i++)
    if (frame[i + 1U] != (unsigned char)code[i]) return 0;
  return frame[length + 1U] == ' ' ||
         (frame[length + 1U] == '\r' && frame[length + 2U] == '\n');
}

static unsigned int redis_response_state(const unsigned char *frame,
                                         unsigned int frame_size)
{
  unsigned char type;
  if (!frame || !frame_size) return 0U;
  type = frame[0];

  /* Semantic simple-string and error states make Redis command stages visible. */
  if (resp_simple_payload_is(frame, frame_size, '+', "OK")) return 200U;
  if (resp_simple_payload_is(frame, frame_size, '+', "PONG")) return 201U;
  if (resp_simple_payload_is(frame, frame_size, '+', "QUEUED")) return 202U;
  if (resp_error_has_code(frame, frame_size, "NOAUTH")) return 300U;
  if (resp_error_has_code(frame, frame_size, "WRONGPASS")) return 301U;
  if (resp_error_has_code(frame, frame_size, "NOPERM")) return 302U;
  if (type == '-') return 303U;

  /* Fallback states preserve RESP2/RESP3 top-level type distinctions. */
  switch (type) {
    case ':': return 210U;
    case '$': return 220U;
    case '*': return 230U;
    case '%': return 231U;
    case '~': return 232U;
    case '|': return 233U;
    case '>': return 234U;
    case '!': return 235U;
    case '=': return 236U;
    case '_': return 237U;
    case '#': return 238U;
    case ',': return 239U;
    case '(': return 240U;
    case '+': return 203U;
    default: return 299U;
  }
}

unsigned int *extract_response_codes_redis(unsigned char *buf,
                                           unsigned int buf_size,
                                           unsigned int *state_count_ref)
{
  unsigned int *states, count = 1, cursor = 0;

  if (!state_count_ref) return NULL;
  states = (unsigned int *)ck_alloc(sizeof(unsigned int));
  states[0] = 0;
  if (!buf || !buf_size) {
    *state_count_ref = count;
    return states;
  }

  while (cursor < buf_size) {
    unsigned int frame_size = 0;
    if (!resp_parse_frame(buf + cursor, buf_size - cursor, &frame_size) ||
        !frame_size)
      break;
    states = (unsigned int *)ck_realloc(states, (count + 1U) * sizeof(unsigned int));
    states[count++] = redis_response_state(buf + cursor, frame_size);
    cursor += frame_size;
  }
  *state_count_ref = count;
  return states;
}
