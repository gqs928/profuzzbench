/* AFLNet request/state adapter for the NNTP reader protocol. */
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

static void append_region(region_t **regions, unsigned int *count,
                          unsigned int start, unsigned int end)
{
  *regions = (region_t *)ck_realloc(*regions, (*count + 1) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

region_t *extract_requests_nntp(unsigned char *buf, unsigned int buf_size,
                                unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0, start = 0, i;
  if (!buf || !buf_size) {
    *region_count_ref = 0;
    return NULL;
  }
  for (i = 0; i + 1 < buf_size; i++) {
    if (buf[i] == '\r' && buf[i + 1] == '\n') {
      append_region(&regions, &count, start, i + 1);
      start = i + 2;
      i++;
    }
  }
  /* Preserve a malformed unterminated command as one final region. */
  if (start < buf_size) append_region(&regions, &count, start, buf_size - 1);
  *region_count_ref = count;
  return regions;
}

static void append_state(unsigned int **states, unsigned int *count,
                         unsigned int state)
{
  *states = (unsigned int *)ck_realloc(*states,
                                       (*count + 1) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

static int multiline_code(unsigned int code)
{
  /* NNTP commands whose response is followed by a dot-terminated block. */
  switch (code) {
    case 100: case 101: case 215: case 220: case 221:
    case 222: case 224: case 230: case 231: case 282:
      return 1;
    default:
      return 0;
  }
}

unsigned int *extract_response_codes_nntp(unsigned char *buf,
                                          unsigned int buf_size,
                                          unsigned int *state_count_ref)
{
  unsigned int *states = NULL, count = 0, start = 0, i;
  int in_multiline = 0;
  append_state(&states, &count, 0);
  for (i = 0; buf && i + 1 < buf_size; i++) {
    if (buf[i] == '\r' && buf[i + 1] == '\n') {
      unsigned int length = i - start;
      if (length == 1 && buf[start] == '.') {
        if (in_multiline) append_state(&states, &count, 2000);
        in_multiline = 0;
      } else if (!in_multiline && length >= 4 &&
                 buf[start] >= '0' && buf[start] <= '9' &&
                 buf[start + 1] >= '0' && buf[start + 1] <= '9' &&
                 buf[start + 2] >= '0' && buf[start + 2] <= '9' &&
                 (buf[start + 3] == ' ' || buf[start + 3] == '-')) {
        unsigned int code = (buf[start] - '0') * 100u +
                            (buf[start + 1] - '0') * 10u +
                            (buf[start + 2] - '0');
        append_state(&states, &count, 1000u + code);
        in_multiline = multiline_code(code);
      }
      start = i + 2;
      i++;
    }
  }
  *state_count_ref = count;
  return states;
}
