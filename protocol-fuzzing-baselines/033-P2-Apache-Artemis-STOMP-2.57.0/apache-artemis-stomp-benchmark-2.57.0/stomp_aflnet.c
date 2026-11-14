/* STOMP frame/request and response-command adapter for AFLNet. */
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

static void stomp_append_region(region_t **regions, unsigned int *count,
                                unsigned int start, unsigned int end) {
  *regions = (region_t *)ck_realloc(*regions, (*count + 1) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

region_t *extract_requests_stomp(unsigned char *buf, unsigned int buf_size,
                                 unsigned int *region_count_ref) {
  region_t *regions = NULL;
  unsigned int count = 0, offset = 0;
  if (!buf || !buf_size) { *region_count_ref = 0; return NULL; }
  while (offset < buf_size) {
    unsigned int end = offset;
    while (end < buf_size && buf[end] != 0) end++;
    if (end < buf_size) {
      stomp_append_region(&regions, &count, offset, end);
      offset = end + 1;
    } else {
      /* Keep an unterminated/truncated tail as a mutable region. */
      stomp_append_region(&regions, &count, offset, buf_size - 1);
      break;
    }
  }
  *region_count_ref = count;
  return regions;
}

static unsigned int stomp_state_for_command(const unsigned char *p,
                                             unsigned int len) {
#define CMD(s, n) (len >= sizeof(n)-1 && !memcmp(p, n, sizeof(n)-1) ? (s) : 0)
  unsigned int state;
  state = CMD(100, "CONNECTED"); if (state) return state;
  state = CMD(101, "MESSAGE"); if (state) return state;
  state = CMD(102, "RECEIPT"); if (state) return state;
  state = CMD(199, "ERROR"); if (state) return state;
  return 1999;
#undef CMD
}

unsigned int *extract_response_codes_stomp(unsigned char *buf,
                                           unsigned int buf_size,
                                           unsigned int *state_count_ref) {
  unsigned int *states = NULL, count = 0, offset = 0;
  states = (unsigned int *)ck_realloc(states, sizeof(unsigned int));
  states[count++] = 0;
  while (buf && offset < buf_size) {
    unsigned int end = offset, line_end;
    while (end < buf_size && buf[end] != 0) end++;
    if (end == offset) { offset++; continue; } /* heartbeat / empty frame */
    /* STOMP peers may emit CR/LF heartbeat bytes before a frame. */
    while (offset < end && (buf[offset] == '\r' || buf[offset] == '\n')) offset++;
    if (offset == end) { offset = end + (end < buf_size); continue; }
    line_end = offset;
    while (line_end < end && buf[line_end] != '\n' && buf[line_end] != '\r') line_end++;
    states = (unsigned int *)ck_realloc(states, (count + 1) * sizeof(unsigned int));
    states[count++] = stomp_state_for_command(buf + offset, line_end - offset);
    if (end == buf_size) break;
    offset = end + 1;
  }
  *state_count_ref = count;
  return states;
}
