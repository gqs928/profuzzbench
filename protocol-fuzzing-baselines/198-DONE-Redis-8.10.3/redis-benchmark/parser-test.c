#include <stdio.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static int check_regions(unsigned char *buf, unsigned int size,
                         const int *starts, const int *ends,
                         unsigned int expected_count)
{
  unsigned int count = 0, i;
  region_t *regions = extract_requests_redis(buf, size, &count);
  int ok = count == expected_count;

  if (ok) {
    for (i = 0; i < count; i++) {
      if (regions[i].start_byte != starts[i] || regions[i].end_byte != ends[i]) {
        fprintf(stderr, "region %u: got %d..%d, expected %d..%d\n", i,
                regions[i].start_byte, regions[i].end_byte,
                starts[i], ends[i]);
        ok = 0;
        break;
      }
    }
  }
  ck_free(regions);
  return ok;
}

int main(void)
{
  /* The bulk value embeds a complete-looking PING request. */
  unsigned char requests[] =
      "*3\r\n$3\r\nSET\r\n$1\r\nk\r\n$14\r\n*1\r\n$4\r\nPING\r\n\r\n"
      "*1\r\n$4\r\nPING\r\n";
  unsigned char streamed[] = "*?\r\n$4\r\nPING\r\n.\r\n";
  unsigned char incomplete[] = "*2\r\n$4\r\nPING\r\n$5\r\nxy";
  unsigned char malformed[] = "*1\r\n$3\r\nGETx";
  unsigned char response[] =
      "+PONG\r\n"
      "*2\r\n$3\r\nfoo\r\n:42\r\n"
      "%1\r\n+key\r\n#t\r\n"
      "#t\r\n"
      "$?\r\n;3\r\nfoo\r\n;0\r\n";
  const int request_starts[] = {0, 41};
  const int request_ends[] = {40, 54};
  const int one_start[] = {0};
  const int streamed_end[] = {16};
  const int incomplete_end[] = {(int)sizeof(incomplete) - 2};
  const int malformed_end[] = {(int)sizeof(malformed) - 2};
  const unsigned int expected_states[] = {0, 201, 230, 231, 238, 220};
  unsigned char semantic_response[] =
      "+OK\r\n+PONG\r\n+QUEUED\r\n"
      "-NOAUTH Authentication required.\r\n"
      "-WRONGPASS invalid username-password pair.\r\n"
      ":1\r\n$1\r\nx\r\n";
  const unsigned int expected_semantic_states[] = {
      0, 200, 201, 202, 300, 301, 210, 220};
  unsigned int state_count = 0, i;
  unsigned int *states;

  if (!check_regions(requests, sizeof(requests) - 1U,
                     request_starts, request_ends, 2)) {
    fprintf(stderr, "bulk payload boundary test failed\n");
    return 1;
  }
  if (!check_regions(streamed, sizeof(streamed) - 1U,
                     one_start, streamed_end, 1)) {
    fprintf(stderr, "streamed aggregate test failed\n");
    return 1;
  }
  if (!check_regions(incomplete, sizeof(incomplete) - 1U,
                     one_start, incomplete_end, 1)) {
    fprintf(stderr, "incomplete request tail test failed\n");
    return 1;
  }
  if (!check_regions(malformed, sizeof(malformed) - 1U,
                     one_start, malformed_end, 1)) {
    fprintf(stderr, "malformed request tail test failed\n");
    return 1;
  }

  states = extract_response_codes_redis(response, sizeof(response) - 1U,
                                        &state_count);
  if (state_count != sizeof(expected_states) / sizeof(expected_states[0])) {
    fprintf(stderr, "response state count: got %u\n", state_count);
    return 1;
  }
  for (i = 0; i < state_count; i++) {
    if (states[i] != expected_states[i]) {
      fprintf(stderr, "response state %u: got %u, expected %u\n",
              i, states[i], expected_states[i]);
      ck_free(states);
      return 1;
    }
  }
  ck_free(states);

  states = extract_response_codes_redis(semantic_response,
                                        sizeof(semantic_response) - 1U,
                                        &state_count);
  if (state_count != sizeof(expected_semantic_states) /
                         sizeof(expected_semantic_states[0])) {
    fprintf(stderr, "semantic response state count: got %u\n", state_count);
    ck_free(states);
    return 1;
  }
  for (i = 0; i < state_count; i++) {
    if (states[i] != expected_semantic_states[i]) {
      fprintf(stderr, "semantic response state %u: got %u, expected %u\n",
              i, states[i], expected_semantic_states[i]);
      ck_free(states);
      return 1;
    }
  }
  ck_free(states);
  puts("PASS: RESP2/RESP3 framing, bulk boundaries, streamed values and response states.");
  return 0;
}
