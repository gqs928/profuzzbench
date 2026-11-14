#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "types.h"
#include "aflnet.h"

void *ck_realloc(void *ptr, size_t size) {
  void *next = realloc(ptr, size);
  if (!next && size) abort();
  return next;
}
void ck_free(void *ptr) { free(ptr); }

#include "nats_aflnet.inc"

static int fail(const char *message) {
  fprintf(stderr, "FAIL: %s\n", message);
  return 1;
}

int main(void) {
  static unsigned char request[] =
      "CONNECT {\"verbose\":true}\r\n"
      "SUB bench.foo 1\r\n"
      "PUB bench.foo 5\r\nhello\r\n"
      "HPUB bench.foo 25 30\r\n"
      "NATS/1.0\r\nX-Test: yes\r\n\r\nhello\r\n"
      "PING\r\n";
  static unsigned char response[] =
      "INFO {\"server_id\":\"test\"}\r\n"
      "+OK\r\nPONG\r\n"
      "MSG bench.foo 1 5\r\nhello\r\n"
      "HMSG bench.foo 1 25 30\r\n"
      "NATS/1.0\r\nX-Test: yes\r\n\r\nhello\r\n"
      "-ERR 'bad request'\r\n";
  unsigned int region_count = 0, state_count = 0, offset = 0, i;
  region_t *regions = extract_requests_nats(request, sizeof(request) - 1,
                                            &region_count);
  unsigned int *states = extract_response_codes_nats(response,
                                                       sizeof(response) - 1,
                                                       &state_count);
  if (region_count != 5) return fail("expected five request regions");
  for (i = 0; i < region_count; ++i) {
    if ((unsigned int)regions[i].start_byte != offset ||
        regions[i].end_byte < regions[i].start_byte ||
        !regions[i].modifiable)
      return fail("request regions are not contiguous and frame-aligned");
    offset = (unsigned int)regions[i].end_byte + 1U;
  }
  if (offset != sizeof(request) - 1U)
    return fail("request parser did not preserve the full stream");
  if (state_count != 7 || states[1] != 0x4e01U || states[2] != 0x4e02U ||
      states[3] != 0x4e04U || states[4] != 0x4e06U ||
      states[5] != 0x4e07U || states[6] != 0x4e03U)
    return fail("response event states or payload framing are incorrect");
  free(regions);
  free(states);
  puts("PASS: NATS CRLF framing, PUB/HPUB payloads, and response-state parser");
  return 0;
}
