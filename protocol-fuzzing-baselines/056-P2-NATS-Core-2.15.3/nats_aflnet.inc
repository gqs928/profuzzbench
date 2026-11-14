/* NATS text protocol framing: CRLF control lines plus length-delimited PUB/HPUB payloads. */
#include <ctype.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>

#define NATS_MAX_PAYLOAD (16U * 1024U * 1024U)

static unsigned int nats_find_crlf(const unsigned char *buf, unsigned int start,
                                   unsigned int size) {
  unsigned int i;
  for (i = start; i + 1 < size; ++i)
    if (buf[i] == '\r' && buf[i + 1] == '\n') return i;
  return UINT_MAX;
}

static int nats_token_is(const unsigned char *buf, unsigned int start,
                         unsigned int end, const char *word) {
  unsigned int i;
  size_t n = strlen(word);
  if ((size_t)(end - start) != n) return 0;
  for (i = 0; i < n; ++i)
    if (toupper((unsigned char)buf[start + i]) !=
        toupper((unsigned char)word[i])) return 0;
  return 1;
}

static int nats_read_uint(const unsigned char *buf, unsigned int start,
                          unsigned int end, unsigned int *value) {
  unsigned int i;
  unsigned int out = 0;
  if (start == end) return 0;
  for (i = start; i < end; ++i) {
    unsigned int digit;
    if (buf[i] < '0' || buf[i] > '9') return 0;
    digit = (unsigned int)(buf[i] - '0');
    if (out > (UINT_MAX - digit) / 10U) return 0;
    out = out * 10U + digit;
  }
  *value = out;
  return 1;
}

/* Read the last one or two decimal tokens from a command line. */
static unsigned int nats_tail_numbers(const unsigned char *buf,
                                      unsigned int start, unsigned int end,
                                      unsigned int wanted,
                                      unsigned int values[2]) {
  unsigned int token_starts[16], token_ends[16], count = 0, i = start;
  if (wanted == 0 || wanted > 2) return 0;
  while (i < end) {
    while (i < end && isspace((unsigned char)buf[i])) ++i;
    if (i == end) break;
    if (count == 16) return 0;
    token_starts[count] = i;
    while (i < end && !isspace((unsigned char)buf[i])) ++i;
    token_ends[count++] = i;
  }
  if (count < wanted) return 0;
  for (i = 0; i < wanted; ++i) {
    unsigned int pos = count - wanted + i;
    if (!nats_read_uint(buf, token_starts[pos], token_ends[pos], &values[i]))
      return 0;
  }
  return wanted;
}

static int nats_payload_command(const unsigned char *buf, unsigned int start,
                                unsigned int line_end,
                                unsigned int *payload_size) {
  unsigned int token_end = start, values[2] = {0, 0}, wanted;
  while (token_end < line_end && !isspace((unsigned char)buf[token_end]))
    ++token_end;
  if (nats_token_is(buf, start, token_end, "PUB")) wanted = 1;
  else if (nats_token_is(buf, start, token_end, "HPUB")) wanted = 2;
  else return 0;
  if (nats_tail_numbers(buf, start, line_end, wanted, values) != wanted)
    return -1;
  *payload_size = wanted == 1 ? values[0] : values[1];
  return 1;
}

static void nats_add_region(region_t **regions, unsigned int *count,
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

region_t *extract_requests_nats(unsigned char *buf, unsigned int buf_size,
                                unsigned int *region_count_ref) {
  region_t *regions = NULL;
  unsigned int count = 0, offset = 0;
  *region_count_ref = 0;
  while (offset < buf_size) {
    unsigned int line_end = nats_find_crlf(buf, offset, buf_size);
    unsigned int payload_size = 0;
    int payload_command;
    if (line_end == UINT_MAX) {
      nats_add_region(&regions, &count, offset, buf_size - 1U);
      break;
    }
    payload_command = nats_payload_command(buf, offset, line_end,
                                           &payload_size);
    if (payload_command < 0 ||
        (payload_command > 0 && payload_size > NATS_MAX_PAYLOAD)) {
      nats_add_region(&regions, &count, offset, buf_size - 1U);
      break;
    }
    if (payload_command == 0) {
      nats_add_region(&regions, &count, offset, line_end + 1U);
      offset = line_end + 2U;
      continue;
    }
    {
      unsigned int message_start = offset;
      unsigned int body_start = line_end + 2U;
      unsigned int remaining = buf_size - body_start;
      if (payload_size > UINT_MAX - 2U || remaining < payload_size + 2U) {
        nats_add_region(&regions, &count, offset, buf_size - 1U);
        break;
      }
      offset = body_start + payload_size + 2U;
      nats_add_region(&regions, &count, message_start, offset - 1U);
    }
  }
  *region_count_ref = count;
  return regions;
}

static void nats_add_state(unsigned int **states, unsigned int *count,
                           unsigned int state) {
  *states = (unsigned int *)ck_realloc(
      *states, ((size_t)*count + 1U) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

static unsigned int nats_state_for_line(const unsigned char *buf,
                                        unsigned int start,
                                        unsigned int end) {
  unsigned int token_end = start;
  while (token_end < end && !isspace((unsigned char)buf[token_end])) ++token_end;
  if (nats_token_is(buf, start, token_end, "INFO")) return 0x4e01U;
  if (nats_token_is(buf, start, token_end, "+OK")) return 0x4e02U;
  if (nats_token_is(buf, start, token_end, "-ERR")) return 0x4e03U;
  if (nats_token_is(buf, start, token_end, "PONG")) return 0x4e04U;
  if (nats_token_is(buf, start, token_end, "PING")) return 0x4e05U;
  if (nats_token_is(buf, start, token_end, "MSG")) return 0x4e06U;
  if (nats_token_is(buf, start, token_end, "HMSG")) return 0x4e07U;
  return 0x4effU;
}

unsigned int *extract_response_codes_nats(unsigned char *buf,
                                           unsigned int buf_size,
                                           unsigned int *state_count_ref) {
  unsigned int *states = NULL;
  unsigned int count = 0, offset = 0;
  *state_count_ref = 0;
  nats_add_state(&states, &count, 0U);
  while (offset < buf_size) {
    unsigned int line_end = nats_find_crlf(buf, offset, buf_size);
    unsigned int payload_size = 0, token_end = offset;
    int payload_command;
    if (line_end == UINT_MAX) {
      nats_add_state(&states, &count, 0x4ffeU);
      break;
    }
    nats_add_state(&states, &count,
                   nats_state_for_line(buf, offset, line_end));
    while (token_end < line_end && !isspace((unsigned char)buf[token_end]))
      ++token_end;
    if (nats_token_is(buf, offset, token_end, "MSG")) {
      unsigned int values[2] = {0, 0};
      if (nats_tail_numbers(buf, offset, line_end, 1, values) != 1)
        payload_command = -1;
      else { payload_size = values[0]; payload_command = 1; }
    } else if (nats_token_is(buf, offset, token_end, "HMSG")) {
      unsigned int values[2] = {0, 0};
      if (nats_tail_numbers(buf, offset, line_end, 2, values) != 2)
        payload_command = -1;
      else { payload_size = values[1]; payload_command = 1; }
    } else {
      payload_command = 0;
    }
    if (payload_command < 0 || payload_size > NATS_MAX_PAYLOAD) {
      nats_add_state(&states, &count, 0x4ffeU);
      break;
    }
    if (payload_command == 0) {
      offset = line_end + 2U;
      continue;
    }
    {
      unsigned int body_start = line_end + 2U;
      unsigned int remaining = buf_size - body_start;
      if (payload_size > UINT_MAX - 2U || remaining < payload_size + 2U) {
        nats_add_state(&states, &count, 0x4ffeU);
        break;
      }
      offset = body_start + payload_size + 2U;
    }
  }
  *state_count_ref = count;
  return states;
}
