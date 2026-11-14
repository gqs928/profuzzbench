/* Cassandra Native Protocol v4/v5 framing adapter for AFLNet. */
#include <stddef.h>
#include <stdint.h>

static uint32_t cql_read_u32be(const unsigned char *p) {
  return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
         ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static void cql_add_region(region_t **regions, unsigned int *count,
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

region_t *extract_requests_cassandra(unsigned char *buf, unsigned int buf_size,
                                     unsigned int *region_count_ref) {
  region_t *regions = NULL;
  unsigned int count = 0;
  unsigned int offset = 0;
  *region_count_ref = 0;

  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    if (remaining < 9 || (buf[offset] != 0x04 && buf[offset] != 0x05)) {
      cql_add_region(&regions, &count, offset, buf_size - 1);
      break;
    }
    uint32_t body_size = cql_read_u32be(buf + offset + 5);
    if (body_size > remaining - 9) {
      cql_add_region(&regions, &count, offset, buf_size - 1);
      break;
    }
    unsigned int frame_size = 9U + body_size;
    cql_add_region(&regions, &count, offset, offset + frame_size - 1);
    offset += frame_size;
  }

  *region_count_ref = count;
  return regions;
}

static void cql_add_state(unsigned int **states, unsigned int *count,
                          unsigned int state) {
  *states = (unsigned int *)ck_realloc(
      *states, ((size_t)*count + 1) * sizeof(unsigned int));
  (*states)[*count] = state;
  (*count)++;
}

unsigned int *extract_response_codes_cassandra(unsigned char *buf,
                                                unsigned int buf_size,
                                                unsigned int *state_count_ref) {
  unsigned int *states = NULL;
  unsigned int count = 0;
  unsigned int offset = 0;
  int emitted_malformed = 0;
  *state_count_ref = 0;

  cql_add_state(&states, &count, 0);
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    if (remaining < 9 ||
        (buf[offset] != 0x84 && buf[offset] != 0x85)) {
      if (!emitted_malformed) cql_add_state(&states, &count, 0x1ffffU);
      break;
    }
    uint32_t body_size = cql_read_u32be(buf + offset + 5);
    if (body_size > remaining - 9) {
      if (!emitted_malformed) cql_add_state(&states, &count, 0x1ffffU);
      break;
    }

    unsigned int opcode = buf[offset + 4];
    unsigned int state = opcode;
    if (opcode == 0x00 && body_size >= 4) {
      state = 0x10000U | (cql_read_u32be(buf + offset + 9) & 0xffffU);
    }
    cql_add_state(&states, &count, state);
    offset += 9U + body_size;
  }

  *state_count_ref = count;
  return states;
}
