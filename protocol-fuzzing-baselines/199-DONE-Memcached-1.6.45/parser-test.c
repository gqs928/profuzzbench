#include <stdio.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

int main(void)
{
  /* The four-byte value contains CRLF, which must not split a storage body. */
  unsigned char request[] = "set k 0 0 4\r\nx\r\ny\r\nget k\r\n";
  unsigned char response[] = "STORED\r\nVALUE k 0 4\r\nx\r\ny\r\nEND\r\nDELETED\r\nEND\r\n";
  unsigned int region_count = 0, state_count = 0, i;
  const unsigned int expected_states[] = {0, 5, 3, 4, 9, 4};
  region_t *regions = extract_requests_memcached(request, sizeof(request) - 1,
                                                  &region_count);
  unsigned int *states = extract_response_codes_memcached(response,
                                                           sizeof(response) - 1,
                                                           &state_count);

  if (region_count != 2 || regions[0].start_byte != 0 ||
      regions[0].end_byte != 18 || regions[1].start_byte != 19 ||
      regions[1].end_byte != (int)sizeof(request) - 2) {
    fprintf(stderr, "request parser boundary test failed (regions=%u)\n", region_count);
    return 1;
  }
  if (state_count != sizeof(expected_states) / sizeof(expected_states[0])) {
    fprintf(stderr, "response parser state count failed (%u)\n", state_count);
    return 1;
  }
  for (i = 0; i < state_count; i++) {
    if (states[i] != expected_states[i]) {
      fprintf(stderr, "response parser state %u: got %u, expected %u\n",
              i, states[i], expected_states[i]);
      return 1;
    }
  }
  ck_free(states);
  ck_free(regions);
  puts("PASS: Memcached parser respects byte-counted request/value bodies and maps response states.");
  return 0;
}
