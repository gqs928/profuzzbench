/* AFLNet request/response parsing for the Memcached ASCII protocol.
 * Scope is intentionally ASCII over TCP; the binary protocol and UDP are
 * outside this benchmark's target configuration. */
#include <limits.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static int mc_find_crlf(const unsigned char *buf, unsigned int start,
                        unsigned int size)
{
  unsigned int i;
  for (i = start; i + 1 < size; i++)
    if (buf[i] == '\r' && buf[i + 1] == '\n') return (int)i;
  return -1;
}

/* Return 0 for ordinary line commands, 1 for a storage command with a valid
 * byte count, and -1 for a malformed storage header. */
static int mc_storage_length(const unsigned char *buf, unsigned int start,
                             unsigned int end, unsigned int *length_ref)
{
  unsigned int i = start, field = 0, token_start, value = 0;
  int storage;

  while (i < end && buf[i] != ' ' && buf[i] != '\t') i++;
  storage = (i - start == 3 && (!memcmp(buf + start, "set", 3) ||
                                !memcmp(buf + start, "add", 3) ||
                                !memcmp(buf + start, "cas", 3))) ||
            (i - start == 6 && !memcmp(buf + start, "append", 6)) ||
            (i - start == 7 && (!memcmp(buf + start, "replace", 7) ||
                                !memcmp(buf + start, "prepend", 7)));
  if (!storage) return 0;

  while (i < end) {
    while (i < end && (buf[i] == ' ' || buf[i] == '\t')) i++;
    if (i == end) break;
    token_start = i;
    while (i < end && buf[i] != ' ' && buf[i] != '\t') i++;
    /* After the command token: key=0, flags=1, exptime=2, bytes=3. */
    if (field == 3) {
      unsigned int j;
      if (i == token_start) return -1;
      for (j = token_start; j < i; j++) {
        unsigned int digit;
        if (buf[j] < '0' || buf[j] > '9') return -1;
        digit = (unsigned int)(buf[j] - '0');
        if (value > (UINT_MAX - digit) / 10) return -1;
        value = value * 10 + digit;
      }
      *length_ref = value;
      return 1;
    }
    field++;
  }
  return -1;
}

region_t *extract_requests_memcached(unsigned char *buf, unsigned int buf_size,
                                     unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0, start = 0;

  while (start < buf_size) {
    int line_end = mc_find_crlf(buf, start, buf_size);
    unsigned int next, body_bytes = 0;
    int storage;

    if (line_end < 0) {
      next = buf_size;
    } else {
      next = (unsigned int)line_end + 2;
      storage = mc_storage_length(buf, start, (unsigned int)line_end,
                                  &body_bytes);
      if (storage > 0) {
        unsigned int body_start = next;
        if (body_bytes <= buf_size - body_start &&
            buf_size - body_start - body_bytes >= 2 &&
            buf[body_start + body_bytes] == '\r' &&
            buf[body_start + body_bytes + 1] == '\n') {
          next = body_start + body_bytes + 2;
        } else {
          /* Keep malformed/incomplete bodies in this region instead of
           * mistaking payload bytes for subsequent command lines. */
          next = buf_size;
        }
      } else if (storage < 0) {
        next = buf_size;
      }
    }

    regions = (region_t *)ck_realloc(regions, (count + 1) * sizeof(region_t));
    regions[count].start_byte = (int)start;
    regions[count].end_byte = (int)(next - 1);
    regions[count].modifiable = 1;
    regions[count].state_sequence = NULL;
    regions[count].state_count = 0;
    count++;
    start = next;
  }

  *region_count_ref = count;
  return regions;
}

static unsigned int mc_response_state(const unsigned char *buf,
                                     unsigned int start, unsigned int end)
{
  unsigned int n = 0;
  while (start + n < end && buf[start + n] != ' ' && buf[start + n] != '\t') n++;
#define MC_STATE(word, id) \
  if (n == sizeof(word) - 1 && !memcmp(buf + start, word, n)) return id
  MC_STATE("VERSION", 1);
  MC_STATE("STAT", 2);
  MC_STATE("VALUE", 3);
  MC_STATE("END", 4);
  MC_STATE("STORED", 5);
  MC_STATE("NOT_STORED", 6);
  MC_STATE("EXISTS", 7);
  MC_STATE("NOT_FOUND", 8);
  MC_STATE("DELETED", 9);
  MC_STATE("TOUCHED", 10);
  MC_STATE("OK", 11);
  MC_STATE("ERROR", 12);
  MC_STATE("CLIENT_ERROR", 13);
  MC_STATE("SERVER_ERROR", 14);
#undef MC_STATE
  return 99; /* Unknown/future ASCII status. */
}

static int mc_value_bytes(const unsigned char *buf, unsigned int start,
                          unsigned int end, unsigned int *bytes_ref)
{
  unsigned int i = start, field = 0, value = 0, token_start;
  while (i < end && buf[i] != ' ' && buf[i] != '\t') i++;
  while (i < end) {
    while (i < end && (buf[i] == ' ' || buf[i] == '\t')) i++;
    if (i == end) break;
    token_start = i;
    while (i < end && buf[i] != ' ' && buf[i] != '\t') i++;
    /* After VALUE: key=0, flags=1, bytes=2. */
    if (field == 2) {
      unsigned int j;
      if (i == token_start) return 0;
      for (j = token_start; j < i; j++) {
        unsigned int digit;
        if (buf[j] < '0' || buf[j] > '9') return 0;
        digit = (unsigned int)(buf[j] - '0');
        if (value > (UINT_MAX - digit) / 10) return 0;
        value = value * 10 + digit;
      }
      *bytes_ref = value;
      return 1;
    }
    field++;
  }
  return 0;
}

unsigned int *extract_response_codes_memcached(unsigned char *buf,
                                                unsigned int buf_size,
                                                unsigned int *state_count_ref)
{
  unsigned int *states, count = 1, cursor = 0;
  states = (unsigned int *)ck_alloc(sizeof(unsigned int));
  states[0] = 0; /* AFLNet's initial protocol state. */

  while (cursor < buf_size) {
    int line_end = mc_find_crlf(buf, cursor, buf_size);
    unsigned int state;
    if (line_end < 0) break;
    state = mc_response_state(buf, cursor, (unsigned int)line_end);
    states = (unsigned int *)ck_realloc(states, (count + 1) * sizeof(unsigned int));
    states[count++] = state;

    if (state == 3) {
      unsigned int body_bytes;
      if (mc_value_bytes(buf, cursor, (unsigned int)line_end, &body_bytes)) {
        unsigned int body_start = (unsigned int)line_end + 2;
        if (body_bytes <= buf_size - body_start &&
            buf_size - body_start - body_bytes >= 2 &&
            buf[body_start + body_bytes] == '\r' &&
            buf[body_start + body_bytes + 1] == '\n') {
          cursor = body_start + body_bytes + 2;
          continue;
        }
      }
    }
    cursor = (unsigned int)line_end + 2;
  }

  *state_count_ref = count;
  return states;
}
