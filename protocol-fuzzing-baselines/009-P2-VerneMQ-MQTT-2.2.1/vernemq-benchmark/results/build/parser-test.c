#include <stdio.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static int check_regions(unsigned char *buf, unsigned int size,
                         const int *starts, const int *ends,
                         unsigned int expected_count)
{
  unsigned int count = 0, i;
  region_t *regions = extract_requests_mqtt(buf, size, &count);
  int ok = count == expected_count;

  if (ok) {
    for (i = 0; i < count; i++) {
      if (regions[i].start_byte != starts[i] ||
          regions[i].end_byte != ends[i]) {
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
  /* The first PUBLISH payload contains bytes that look like another packet. */
  unsigned char requests[] = {
    0x30, 0x05, 0x00, 0x01, 'a', 0xc0, 0x00,
    0xc0, 0x00
  };
  /* Unknown packet type with a two-byte Remaining Length (131 bytes total). */
  unsigned char long_packet[134] = {0xf0, 0x83, 0x01};
  unsigned char incomplete[] = {0x30, 0x05, 0x00, 0x01, 'a', 0x01};
  unsigned char bad_length[] = {0x30, 0x80, 0x80, 0x80, 0x80, 0x00};
  unsigned char response[] = {
    0x20, 0x02, 0x00, 0x00,       /* CONNACK success */
    0x90, 0x03, 0x00, 0x01, 0x00, /* SUBACK */
    0xd0, 0x00                    /* PINGRESP */
  };
  const int request_starts[] = {0, 7};
  const int request_ends[] = {6, 8};
  const int long_starts[] = {0};
  const int long_ends[] = {133};
  const int tail_starts[] = {0};
  const int tail_ends[] = {5};
  const unsigned int expected_states[] = {0, 2000, 109, 113};
  unsigned int state_count = 0, i;
  unsigned int *states;

  if (!check_regions(requests, sizeof(requests), request_starts, request_ends, 2)) {
    fprintf(stderr, "packet payload boundary test failed\n");
    return 1;
  }
  if (!check_regions(long_packet, sizeof(long_packet), long_starts, long_ends, 1)) {
    fprintf(stderr, "two-byte Remaining Length test failed\n");
    return 1;
  }
  if (!check_regions(incomplete, sizeof(incomplete), tail_starts, tail_ends, 1)) {
    fprintf(stderr, "incomplete packet tail test failed\n");
    return 1;
  }
  if (!check_regions(bad_length, sizeof(bad_length), tail_starts, tail_ends, 1)) {
    fprintf(stderr, "malformed Remaining Length tail test failed\n");
    return 1;
  }

  states = extract_response_codes_mqtt(response, sizeof(response), &state_count);
  if (state_count != sizeof(expected_states) / sizeof(expected_states[0])) {
    fprintf(stderr, "response state count: got %u\n", state_count);
    return 1;
  }
  for (i = 0; i < state_count; i++) {
    if (states[i] != expected_states[i]) {
      fprintf(stderr, "response state %u: got %u, expected %u\n",
              i, states[i], expected_states[i]);
      return 1;
    }
  }
  ck_free(states);
  puts("PASS: MQTT packet framing, payload boundaries, partial tails and response states.");
  return 0;
}
