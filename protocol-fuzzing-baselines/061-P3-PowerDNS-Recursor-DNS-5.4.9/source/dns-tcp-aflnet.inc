/* DNS message framing for DNS-over-TCP (RFC 7766) and response-state feedback. */
#include <stddef.h>
#include <stdint.h>

static unsigned int dns_tcp_read_u16(const unsigned char *p) {
  return ((unsigned int)p[0] << 8) | (unsigned int)p[1];
}

static void dns_tcp_add_region(region_t **regions, unsigned int *count,
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

region_t *extract_requests_dns_tcp(unsigned char *buf, unsigned int buf_size,
                                   unsigned int *region_count_ref) {
  region_t *regions = NULL;
  unsigned int count = 0U, offset = 0U;
  *region_count_ref = 0U;
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    unsigned int message_length;
    if (remaining < 2U) {
      dns_tcp_add_region(&regions, &count, offset, buf_size - 1U);
      break;
    }
    message_length = dns_tcp_read_u16(buf + offset);
    if (message_length < 12U || message_length > remaining - 2U) {
      /* Keep malformed/truncated tail intact so the server can process it. */
      dns_tcp_add_region(&regions, &count, offset, buf_size - 1U);
      break;
    }
    dns_tcp_add_region(&regions, &count, offset,
                       offset + 1U + message_length);
    offset += 2U + message_length;
  }
  *region_count_ref = count;
  return regions;
}

static void dns_tcp_add_state(unsigned int **states, unsigned int *count,
                              unsigned int state) {
  *states = (unsigned int *)ck_realloc(
      *states, ((size_t)*count + 1U) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

unsigned int *extract_response_codes_dns_tcp(unsigned char *buf,
                                              unsigned int buf_size,
                                              unsigned int *state_count_ref) {
  unsigned int *states = NULL;
  unsigned int count = 0U, offset = 0U;
  *state_count_ref = 0U;
  if (buf_size == 0U) return NULL;
  dns_tcp_add_state(&states, &count, 0U);
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    unsigned int message_length, flags;
    if (remaining < 2U) {
      dns_tcp_add_state(&states, &count, 0xD3FFFFU);
      break;
    }
    message_length = dns_tcp_read_u16(buf + offset);
    if (message_length < 12U || message_length > remaining - 2U) {
      dns_tcp_add_state(&states, &count, 0xD3FFFFU);
      break;
    }
    flags = dns_tcp_read_u16(buf + offset + 4U);
    /* QR, opcode, AA, TC, and RCODE are protocol states; ignore volatile ID/RD. */
    dns_tcp_add_state(&states, &count, 0xD3000000U | (flags & 0xFE0FU));
    offset += 2U + message_length;
  }
  *state_count_ref = count;
  return states;
}
