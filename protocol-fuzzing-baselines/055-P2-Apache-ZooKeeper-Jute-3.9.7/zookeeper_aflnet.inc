/* Apache ZooKeeper Jute length-prefix framing and ReplyHeader feedback. */
#include <stddef.h>
#include <stdint.h>

#define ZK_MAX_FRAME (16U * 1024U * 1024U)

static uint32_t zk_read_u32be(const unsigned char *p) {
  return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
         ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static void zk_add_region(region_t **regions, unsigned int *count,
                          unsigned int start, unsigned int end) {
  *regions = (region_t *)ck_realloc(*regions,
                                    ((size_t)*count + 1) * sizeof(region_t));
  region_t *region = &(*regions)[*count];
  region->start_byte = (int)start;
  region->end_byte = (int)end;
  region->modifiable = 1;
  region->state_sequence = NULL;
  region->state_count = 0;
  (*count)++;
}

region_t *extract_requests_zookeeper(unsigned char *buf, unsigned int buf_size,
                                     unsigned int *region_count_ref) {
  region_t *regions = NULL;
  unsigned int count = 0;
  unsigned int offset = 0;
  *region_count_ref = 0;
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    if (remaining < 4) {
      zk_add_region(&regions, &count, offset, buf_size - 1);
      break;
    }
    uint32_t body_size = zk_read_u32be(buf + offset);
    if (body_size > ZK_MAX_FRAME || body_size > remaining - 4) {
      zk_add_region(&regions, &count, offset, buf_size - 1);
      break;
    }
    unsigned int frame_size = 4U + body_size;
    zk_add_region(&regions, &count, offset, offset + frame_size - 1);
    offset += frame_size;
  }
  *region_count_ref = count;
  return regions;
}

static void zk_add_state(unsigned int **states, unsigned int *count,
                         unsigned int state) {
  *states = (unsigned int *)ck_realloc(
      *states, ((size_t)*count + 1) * sizeof(unsigned int));
  (*states)[*count] = state;
  (*count)++;
}

unsigned int *extract_response_codes_zookeeper(unsigned char *buf,
                                                unsigned int buf_size,
                                                unsigned int *state_count_ref) {
  unsigned int *states = NULL;
  unsigned int count = 0;
  unsigned int offset = 0;
  *state_count_ref = 0;
  zk_add_state(&states, &count, 0);
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    if (remaining < 4) {
      zk_add_state(&states, &count, 0x1ffffU);
      break;
    }
    uint32_t body_size = zk_read_u32be(buf + offset);
    if (body_size > ZK_MAX_FRAME || body_size > remaining - 4) {
      zk_add_state(&states, &count, 0x1ffffU);
      break;
    }
    /* ConnectResponse is a Jute record without an ordinary ReplyHeader. */
    if (offset == 0 && body_size >= 37 && zk_read_u32be(buf + offset + 4) == 0) {
      zk_add_state(&states, &count, 0x10000U);
    } else if (body_size >= 16) {
      int32_t err = (int32_t)zk_read_u32be(buf + offset + 4 + 12);
      uint32_t payload_size = body_size - 16U;
      unsigned int state;
      if (err != 0) {
        state = 0x30000U | ((uint32_t)err & 0xffffU);
      } else {
        unsigned int payload_class = payload_size == 0 ? 0 :
                                     payload_size <= 4 ? 1 :
                                     payload_size <= 32 ? 2 : 3;
        state = 0x20000U | payload_class;
      }
      zk_add_state(&states, &count, state);
    } else {
      zk_add_state(&states, &count, 0x1fffeU);
    }
    offset += 4U + body_size;
  }
  *state_count_ref = count;
  return states;
}
