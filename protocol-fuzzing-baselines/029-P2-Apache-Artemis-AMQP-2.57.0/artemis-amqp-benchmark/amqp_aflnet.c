/* AMQP 1.0 TCP frame/request and response-performative adapter for AFLNet. */
#include <stdint.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

static uint32_t amqp_be32(const unsigned char *p)
{
  return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
         ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static void amqp_append_region(region_t **regions, unsigned int *count,
                               unsigned int start, unsigned int end)
{
  if (end < start) return;
  *regions = (region_t *)ck_realloc(*regions, (*count + 1) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

region_t *extract_requests_amqp(unsigned char *buf, unsigned int buf_size,
                                unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0, offset = 0;
  if (!buf || !buf_size) {
    *region_count_ref = 0;
    return NULL;
  }
  if (buf_size >= 8 && !memcmp(buf, "AMQP", 4)) {
    amqp_append_region(&regions, &count, 0, 7);
    offset = 8;
  }
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    uint32_t frame_size;
    if (remaining < 4) {
      amqp_append_region(&regions, &count, offset, buf_size - 1);
      break;
    }
    frame_size = amqp_be32(buf + offset);
    if (frame_size < 8 || frame_size > remaining) {
      amqp_append_region(&regions, &count, offset, buf_size - 1);
      break;
    }
    amqp_append_region(&regions, &count, offset,
                       offset + (unsigned int)frame_size - 1);
    offset += (unsigned int)frame_size;
  }
  *region_count_ref = count;
  return regions;
}

static void amqp_append_state(unsigned int **states, unsigned int *count,
                              unsigned int state)
{
  *states = (unsigned int *)ck_realloc(*states, (*count + 1) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

static unsigned int amqp_descriptor(const unsigned char *p, unsigned int n,
                                    int *valid)
{
  unsigned int i;
  *valid = 0;
  if (n >= 3 && p[0] == 0x00 && p[1] == 0x53) {
    *valid = 1;
    return p[2];
  }
  if (n >= 10 && p[0] == 0x00 && p[1] == 0x80) {
    uint64_t value = 0;
    for (i = 0; i < 8; i++) value = (value << 8) | p[2 + i];
    *valid = 1;
    return (unsigned int)(value & 0xFFFFu);
  }
  return 0;
}

unsigned int *extract_response_codes_amqp(unsigned char *buf,
                                          unsigned int buf_size,
                                          unsigned int *state_count_ref)
{
  unsigned int *states = NULL, count = 0, offset = 0;
  amqp_append_state(&states, &count, 0);
  if (buf && buf_size >= 8 && !memcmp(buf, "AMQP", 4)) {
    amqp_append_state(&states, &count, 5000u + buf[4]);
    offset = 8;
  }
  while (buf && offset < buf_size) {
    unsigned int remaining = buf_size - offset, frame_type, doff;
    uint32_t frame_size;
    if (remaining < 8) {
      amqp_append_state(&states, &count, 5299);
      break;
    }
    frame_size = amqp_be32(buf + offset);
    if (frame_size < 8 || frame_size > remaining) {
      amqp_append_state(&states, &count, 5298);
      break;
    }
    doff = buf[offset + 4];
    frame_type = buf[offset + 5];
    if (doff >= 2 && doff * 4u < frame_size) {
      unsigned int payload_offset = offset + doff * 4u;
      unsigned int payload_size = (unsigned int)frame_size - doff * 4u;
      int valid;
      unsigned int descriptor = amqp_descriptor(buf + payload_offset,
                                                 payload_size, &valid);
      if (valid)
        amqp_append_state(&states, &count,
                          (frame_type == 1 ? 6000u : 5000u) + descriptor);
      else
        amqp_append_state(&states, &count, 5200u + frame_type);
    } else {
      amqp_append_state(&states, &count, 5200u + frame_type);
    }
    offset += (unsigned int)frame_size;
  }
  *state_count_ref = count;
  return states;
}
