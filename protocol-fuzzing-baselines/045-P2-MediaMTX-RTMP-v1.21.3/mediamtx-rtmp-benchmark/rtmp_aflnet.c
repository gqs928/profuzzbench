#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include "types.h"
#include "alloc-inl.h"
#include "aflnet.h"

#define RTMP_MAX_CSID 4096U
#define RTMP_DEFAULT_CHUNK 128U
#define RTMP_HANDSHAKE_C1 1537U
#define RTMP_HANDSHAKE_C2 1536U
#define RTMP_HANDSHAKE_REPLY 3073U

typedef struct {
  uint32_t timestamp;
  uint32_t delta;
  uint32_t message_length;
  uint32_t received;
  uint32_t stream_id;
  uint8_t message_type;
  uint8_t valid;
  uint8_t extended_timestamp;
  uint8_t first[16];
  uint32_t first_length;
} rtmp_chunk_stream_t;

static uint32_t
rtmp_u24(const unsigned char *p)
{
  return ((uint32_t)p[0] << 16) | ((uint32_t)p[1] << 8) | (uint32_t)p[2];
}

static uint32_t
rtmp_u32be(const unsigned char *p)
{
  return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
         ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static int
rtmp_basic_header(const unsigned char *buf, uint32_t size, uint32_t *offset,
                  uint8_t *format, uint32_t *csid)
{
  uint8_t first, low;
  if (*offset >= size) return 0;
  first = buf[(*offset)++];
  *format = (uint8_t)(first >> 6);
  low = (uint8_t)(first & 0x3f);
  if (low == 0) {
    if (*offset >= size) return 0;
    *csid = 64U + buf[(*offset)++];
  } else if (low == 1) {
    if (size - *offset < 2) return 0;
    *csid = 64U + buf[*offset] + ((uint32_t)buf[*offset + 1] << 8);
    *offset += 2;
  } else {
    *csid = low;
  }
  return *csid < RTMP_MAX_CSID;
}

static uint32_t
rtmp_state_code(uint8_t type, const unsigned char *body, uint32_t body_length)
{
  uint32_t offset = 0, n, hash = 2166136261U;
  if ((type == 17 || type == 20) && body_length >= 3) {
    if (type == 17 && body[0] == 0) offset = 1;
    if (body_length >= offset + 3 && body[offset] == 2) {
      n = ((uint32_t)body[offset + 1] << 8) | body[offset + 2];
      offset += 3;
      if (n > body_length - offset) n = body_length - offset;
      if (n > 128) n = 128;
      while (n--) hash = (hash ^ body[offset++]) * 16777619U;
      return ((uint32_t)type << 24) | (hash & 0x00ffffffU);
    }
  }
  return 0x00010000U | (uint32_t)type;
}

/* Consume one logical RTMP message, including its fmt=3 continuation chunks. */
static int
rtmp_next_message(const unsigned char *buf, uint32_t size, uint32_t start,
                  uint32_t *chunk_size, rtmp_chunk_stream_t *streams,
                  uint32_t *end, uint8_t *type_out, uint32_t *state_out)
{
  uint32_t pos = start, csid, header_length, timestamp_field;
  uint32_t payload_start, chunk_payload, remaining;
  uint8_t format, type;
  rtmp_chunk_stream_t *stream;
  int new_message = 1;

  if (!rtmp_basic_header(buf, size, &pos, &format, &csid)) return 0;
  stream = &streams[csid];
  if (format == 0) {
    header_length = 11;
    if (size - pos < header_length) return 0;
    timestamp_field = rtmp_u24(buf + pos);
    stream->message_length = rtmp_u24(buf + pos + 3);
    stream->message_type = buf[pos + 6];
    stream->stream_id = (uint32_t)buf[pos + 7] |
                        ((uint32_t)buf[pos + 8] << 8) |
                        ((uint32_t)buf[pos + 9] << 16) |
                        ((uint32_t)buf[pos + 10] << 24);
    pos += header_length;
    stream->extended_timestamp = (timestamp_field == 0x00ffffffU);
    if (stream->extended_timestamp) {
      if (size - pos < 4) return 0;
      timestamp_field = rtmp_u32be(buf + pos);
      pos += 4;
    }
    stream->timestamp = timestamp_field;
    stream->delta = timestamp_field;
    stream->received = 0;
    stream->first_length = 0;
    stream->valid = 1;
  } else if (format == 1 || format == 2) {
    header_length = (format == 1) ? 7 : 3;
    if (!stream->valid || size - pos < header_length) return 0;
    timestamp_field = rtmp_u24(buf + pos);
    if (format == 1) {
      stream->message_length = rtmp_u24(buf + pos + 3);
      stream->message_type = buf[pos + 6];
    }
    pos += header_length;
    stream->extended_timestamp = (timestamp_field == 0x00ffffffU);
    if (stream->extended_timestamp) {
      if (size - pos < 4) return 0;
      timestamp_field = rtmp_u32be(buf + pos);
      pos += 4;
    }
    stream->delta = timestamp_field;
    stream->timestamp += timestamp_field;
    stream->received = 0;
    stream->first_length = 0;
  } else {
    if (!stream->valid) return 0;
    if (stream->received == stream->message_length) {
      stream->timestamp += stream->delta;
      stream->received = 0;
      stream->first_length = 0;
    } else {
      new_message = 0;
    }
    if (stream->extended_timestamp) {
      if (size - pos < 4) return 0;
      pos += 4;
    }
  }
  type = stream->message_type;
  if (new_message && (format != 3) && stream->received != 0) return 0;
  do {
    remaining = stream->message_length - stream->received;
    chunk_payload = remaining < *chunk_size ? remaining : *chunk_size;
    payload_start = pos;
    if (size - pos < chunk_payload) return 0;
    if (stream->first_length < sizeof(stream->first)) {
      uint32_t copy_length = sizeof(stream->first) - stream->first_length;
      if (copy_length > chunk_payload) copy_length = chunk_payload;
      if (copy_length) {
        memcpy(stream->first + stream->first_length, buf + payload_start, copy_length);
        stream->first_length += copy_length;
      }
    }
    pos += chunk_payload;
    stream->received += chunk_payload;
    if (stream->received < stream->message_length) {
      uint32_t continuation_csid;
      uint8_t continuation_format;
      if (!rtmp_basic_header(buf, size, &pos, &continuation_format, &continuation_csid) ||
          continuation_format != 3 || continuation_csid != csid) return 0;
      if (stream->extended_timestamp) {
        if (size - pos < 4) return 0;
        pos += 4;
      }
    }
  } while (stream->received < stream->message_length);

  *end = pos;
  *type_out = type;
  *state_out = rtmp_state_code(type, stream->first, stream->first_length);
  if (type == 1 && stream->first_length >= 4) {
    uint32_t requested = rtmp_u32be(stream->first) & 0x7fffffffU;
    if (requested > 0 && requested <= 0x00100000U) *chunk_size = requested;
  }
  return pos > start;
}

static void
rtmp_add_region(region_t **regions, uint32_t *count, uint32_t start, uint32_t end)
{
  region_t *grown;
  if (end < start) return;
  grown = (region_t *)ck_realloc(*regions, (*count + 1) * sizeof(region_t));
  *regions = grown;
  grown[*count].start_byte = (int)start;
  grown[*count].end_byte = (int)end;
  grown[*count].modifiable = 1;
  grown[*count].state_sequence = NULL;
  grown[*count].state_count = 0;
  (*count)++;
}

region_t *
extract_requests_rtmp(unsigned char *buf, unsigned int buf_size,
                      unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  rtmp_chunk_stream_t *streams;
  uint32_t count = 0, pos = 0, end, chunk_size = RTMP_DEFAULT_CHUNK, state;
  uint8_t type;
  if (!buf_size) {
    *region_count_ref = 0;
    return NULL;
  }
  if (buf_size < RTMP_HANDSHAKE_C1) {
    rtmp_add_region(&regions, &count, 0, buf_size - 1);
    *region_count_ref = count;
    return regions;
  }
  rtmp_add_region(&regions, &count, 0, RTMP_HANDSHAKE_C1 - 1);
  pos = RTMP_HANDSHAKE_C1;
  if (buf_size - pos < RTMP_HANDSHAKE_C2) {
    rtmp_add_region(&regions, &count, pos, buf_size - 1);
    *region_count_ref = count;
    return regions;
  }
  rtmp_add_region(&regions, &count, pos, pos + RTMP_HANDSHAKE_C2 - 1);
  pos += RTMP_HANDSHAKE_C2;
  streams = (rtmp_chunk_stream_t *)calloc(RTMP_MAX_CSID, sizeof(*streams));
  if (!streams) {
    rtmp_add_region(&regions, &count, pos, buf_size - 1);
    *region_count_ref = count;
    return regions;
  }
  while (pos < buf_size) {
    uint32_t before = pos;
    if (!rtmp_next_message(buf, buf_size, pos, &chunk_size, streams, &end, &type, &state) ||
        end <= pos) {
      rtmp_add_region(&regions, &count, pos, buf_size - 1);
      break;
    }
    pos = end;
    rtmp_add_region(&regions, &count, before, pos - 1);
  }
  free(streams);
  *region_count_ref = count;
  return regions;
}

static void
rtmp_add_state(unsigned int **states, unsigned int *count, uint32_t value)
{
  unsigned int *grown = (unsigned int *)ck_realloc(*states, (*count + 1) * sizeof(unsigned int));
  *states = grown;
  grown[*count] = value;
  (*count)++;
}

unsigned int *
extract_response_codes_rtmp(unsigned char *buf, unsigned int buf_size,
                            unsigned int *state_count_ref)
{
  unsigned int *states = NULL, count = 0;
  rtmp_chunk_stream_t *streams;
  uint32_t pos = 0, end, chunk_size = RTMP_DEFAULT_CHUNK, state;
  uint8_t type;
  rtmp_add_state(&states, &count, 0);
  if (buf_size >= RTMP_HANDSHAKE_REPLY && buf[0] == 3) {
    rtmp_add_state(&states, &count, 3);
    pos = RTMP_HANDSHAKE_REPLY;
  }
  streams = (rtmp_chunk_stream_t *)calloc(RTMP_MAX_CSID, sizeof(*streams));
  if (!streams) {
    *state_count_ref = count;
    return states;
  }
  while (pos < buf_size) {
    if (!rtmp_next_message(buf, buf_size, pos, &chunk_size, streams, &end, &type, &state) ||
        end <= pos) break;
    pos = end;
    rtmp_add_state(&states, &count, state);
  }
  free(streams);
  *state_count_ref = count;
  return states;
}
