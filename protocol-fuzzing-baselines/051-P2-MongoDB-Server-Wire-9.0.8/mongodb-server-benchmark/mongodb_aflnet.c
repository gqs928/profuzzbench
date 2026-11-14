/* MongoDB wire adapter: split little-endian frames and classify OP_MSG replies. */
#include <limits.h>
#include <stdint.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

enum {
  MONGO_STATE_INIT = 0U,
  MONGO_STATE_OK = 1U,
  MONGO_STATE_ERROR = 2U,
  MONGO_STATE_OTHER = 3U,
  MONGO_STATE_ERROR_CODE_BASE = 0x10000U
};

enum {
  MONGO_OP_MSG = 2013
};

static uint32_t mongo_u32le(const unsigned char *buf)
{
  return (uint32_t)buf[0] | ((uint32_t)buf[1] << 8) |
         ((uint32_t)buf[2] << 16) | ((uint32_t)buf[3] << 24);
}

static uint64_t mongo_u64le(const unsigned char *buf)
{
  return (uint64_t)mongo_u32le(buf) |
         ((uint64_t)mongo_u32le(buf + 4) << 32);
}

static void mongo_append_region(region_t **regions, unsigned int *count,
                                unsigned int start, unsigned int end)
{
  *regions = (region_t *)ck_realloc(*regions,
                                    (*count + 1U) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1U;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0U;
  (*count)++;
}

region_t *extract_requests_mongodb(unsigned char *buf, unsigned int buf_size,
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

    if (remaining < 16U) {
      mongo_append_region(&regions, &count, cursor, buf_size - 1U);
      break;
    }
    declared = mongo_u32le(buf + cursor);
    if (declared < 16U || declared > remaining || declared > INT_MAX ||
        cursor > (unsigned int)INT_MAX - declared) {
      mongo_append_region(&regions, &count, cursor, buf_size - 1U);
      break;
    }
    mongo_append_region(&regions, &count, cursor, cursor + declared - 1U);
    cursor += declared;
  }

  *region_count_ref = count;
  return regions;
}

/* Return the serialized size of one BSON value, or zero when malformed. */
static unsigned int mongo_bson_value_size(unsigned char type,
                                          const unsigned char *buf,
                                          unsigned int remaining)
{
  uint32_t size;
  const unsigned char *end;

  switch (type) {
    case 0x01: return remaining >= 8U ? 8U : 0U; /* double */
    case 0x02: case 0x0D: case 0x0E: /* string, JavaScript, symbol */
      if (remaining < 4U) return 0U;
      size = mongo_u32le(buf);
      if (size < 1U || size > remaining - 4U) return 0U;
      return size + 4U;
    case 0x03: case 0x04: /* document, array */
      if (remaining < 4U) return 0U;
      size = mongo_u32le(buf);
      if (size < 5U || size > remaining) return 0U;
      return size;
    case 0x05: /* binary */
      if (remaining < 5U) return 0U;
      size = mongo_u32le(buf);
      if (size > remaining - 5U) return 0U;
      return size + 5U;
    case 0x06: case 0x0A: case 0x7F: case 0xFF: return 0U;
    case 0x07: return remaining >= 12U ? 12U : 0U; /* ObjectId */
    case 0x08: return remaining >= 1U ? 1U : 0U;  /* boolean */
    case 0x09: case 0x11: case 0x12:              /* date, timestamp, int64 */
      return remaining >= 8U ? 8U : 0U;
    case 0x0B: /* regex */
      end = (const unsigned char *)memchr(buf, 0, remaining);
      if (!end) return 0U;
      size = (uint32_t)(end - buf) + 1U;
      if (size >= remaining) return 0U;
      end = (const unsigned char *)memchr(buf + size, 0, remaining - size);
      if (!end) return 0U;
      return (uint32_t)(end - buf) + 1U;
    case 0x0C: /* DBPointer */
      if (remaining < 4U) return 0U;
      size = mongo_u32le(buf);
      if (size < 1U || size > remaining - 16U) return 0U;
      return size + 16U;
    case 0x0F: /* JavaScript code with scope: total-size field */
      if (remaining < 4U) return 0U;
      size = mongo_u32le(buf);
      if (size < 4U || size > remaining) return 0U;
      return size;
    case 0x10: return remaining >= 4U ? 4U : 0U; /* int32 */
    case 0x13: return remaining >= 16U ? 16U : 0U; /* decimal128 */
    default: return 0U;
  }
}

static int mongo_find_numeric(const unsigned char *doc, unsigned int doc_size,
                              const char *wanted, int64_t *value)
{
  unsigned int cursor = 4U;

  if (doc_size < 5U || mongo_u32le(doc) != doc_size || doc[doc_size - 1U] != 0U)
    return 0;
  while (cursor < doc_size - 1U) {
    unsigned char type = doc[cursor++];
    const unsigned char *key_end =
        (const unsigned char *)memchr(doc + cursor, 0, doc_size - cursor);
    unsigned int key_size;
    unsigned int data_size;
    const unsigned char *data;

    if (!key_end) return 0;
    key_size = (unsigned int)(key_end - (doc + cursor));
    cursor += key_size + 1U;
    data = doc + cursor;
    data_size = mongo_bson_value_size(type, data, doc_size - 1U - cursor);
    if (!data_size && type != 0x0A && type != 0x06 && type != 0x7F && type != 0xFF)
      return 0;
    if ((strlen(wanted) == key_size &&
         memcmp(doc + cursor - key_size - 1U, wanted, key_size) == 0)) {
      if (type == 0x01 && data_size == 8U) {
        uint64_t bits = mongo_u64le(data);
        double number;
        memcpy(&number, &bits, sizeof(number));
        *value = (int64_t)number;
        return 1;
      }
      if (type == 0x10 && data_size == 4U) {
        *value = (int32_t)mongo_u32le(data);
        return 1;
      }
      if (type == 0x12 && data_size == 8U) {
        *value = (int64_t)mongo_u64le(data);
        return 1;
      }
      if (type == 0x08 && data_size == 1U) {
        *value = data[0] != 0U;
        return 1;
      }
      return 0;
    }
    cursor += data_size;
  }
  return 0;
}

static unsigned int mongo_response_state(const unsigned char *frame,
                                         unsigned int frame_size)
{
  int32_t opcode;
  unsigned int section;
  unsigned int bson_size;
  int64_t ok = 0;
  int64_t code = 0;
  int have_ok;
  int have_code;

  if (frame_size < 21U) return MONGO_STATE_OTHER;
  opcode = (int32_t)mongo_u32le(frame + 12U);
  if (opcode != MONGO_OP_MSG) return MONGO_STATE_OTHER;
  section = 20U;
  if (frame[section] != 0U || frame_size - (section + 1U) < 5U)
    return MONGO_STATE_OTHER;
  bson_size = mongo_u32le(frame + section + 1U);
  if (bson_size > frame_size - (section + 1U)) return MONGO_STATE_OTHER;
  have_ok = mongo_find_numeric(frame + section + 1U, bson_size, "ok", &ok);
  have_code = mongo_find_numeric(frame + section + 1U, bson_size, "code", &code);
  if (!have_ok) return MONGO_STATE_OTHER;
  if (ok != 0) return MONGO_STATE_OK;
  if (have_code && code >= 0 && code < 0x7fff)
    return MONGO_STATE_ERROR_CODE_BASE + (unsigned int)code;
  return MONGO_STATE_ERROR;
}

unsigned int *extract_response_codes_mongodb(unsigned char *buf,
                                             unsigned int buf_size,
                                             unsigned int *state_count_ref)
{
  unsigned int *states;
  unsigned int count = 1U;
  unsigned int cursor = 0U;

  if (!state_count_ref) return NULL;
  states = (unsigned int *)ck_alloc(sizeof(unsigned int));
  states[0] = MONGO_STATE_INIT;
  if (!buf || !buf_size) {
    *state_count_ref = count;
    return states;
  }
  while (buf_size - cursor >= 16U) {
    uint32_t frame_size = mongo_u32le(buf + cursor);
    unsigned int state;
    if (frame_size < 16U || frame_size > buf_size - cursor) break;
    state = mongo_response_state(buf + cursor, frame_size);
    states = (unsigned int *)ck_realloc(states, (count + 1U) * sizeof(unsigned int));
    states[count++] = state;
    cursor += frame_size;
  }
  *state_count_ref = count;
  return states;
}
