/* BGP message framing: 16-byte marker, 2-byte length, 1-byte type. */
#include <stddef.h>
#include <stdint.h>

static unsigned int bgp_read_u16be(const unsigned char *p) {
  return ((unsigned int)p[0] << 8) | (unsigned int)p[1];
}

static void bgp_add_region(region_t **regions, unsigned int *count,
                           unsigned int start, unsigned int end) {
  *regions = (region_t *)ck_realloc(
      *regions, ((size_t)*count + 1U) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  ++*count;
}

region_t *extract_requests_bgp(unsigned char *buf, unsigned int buf_size,
                               unsigned int *region_count_ref) {
  region_t *regions = NULL;
  unsigned int count = 0, offset = 0;
  *region_count_ref = 0;
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    unsigned int message_length;
    if (remaining < 19U) {
      bgp_add_region(&regions, &count, offset, buf_size - 1U);
      break;
    }
    message_length = bgp_read_u16be(buf + offset + 16U);
    if (message_length < 19U || message_length > 65535U ||
        message_length > remaining) {
      bgp_add_region(&regions, &count, offset, buf_size - 1U);
      break;
    }
    bgp_add_region(&regions, &count, offset,
                   offset + message_length - 1U);
    offset += message_length;
  }
  *region_count_ref = count;
  return regions;
}

static void bgp_add_state(unsigned int **states, unsigned int *count,
                          unsigned int state) {
  *states = (unsigned int *)ck_realloc(
      *states, ((size_t)*count + 1U) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

unsigned int *extract_response_codes_bgp(unsigned char *buf,
                                         unsigned int buf_size,
                                         unsigned int *state_count_ref) {
  unsigned int *states = NULL;
  unsigned int count = 0, offset = 0;
  *state_count_ref = 0;
  if (buf_size == 0U) return NULL;
  bgp_add_state(&states, &count, 0U);
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    unsigned int message_length, message_type, state;
    if (remaining < 19U) {
      bgp_add_state(&states, &count, 0xB1FFFFU);
      break;
    }
    message_length = bgp_read_u16be(buf + offset + 16U);
    message_type = buf[offset + 18U];
    if (message_length < 19U || message_length > remaining) {
      bgp_add_state(&states, &count, 0xB1FFFFU);
      break;
    }
    if (message_type == 3U && message_length >= 21U) {
      unsigned int error = buf[offset + 19U];
      unsigned int subcode = buf[offset + 20U];
      state = 0xB30000U | (error << 8) | subcode;
    } else if (message_type >= 1U && message_type <= 5U) {
      state = 0xB10000U | message_type;
    } else {
      state = 0xB1FF00U | message_type;
    }
    bgp_add_state(&states, &count, state);
    offset += message_length;
  }
  *state_count_ref = count;
  return states;
}
