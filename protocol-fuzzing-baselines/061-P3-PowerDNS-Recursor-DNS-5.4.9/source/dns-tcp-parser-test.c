#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct region {
  int start_byte;
  int end_byte;
  int modifiable;
  unsigned int *state_sequence;
  unsigned int state_count;
} region_t;

static void *ck_realloc(void *p, size_t n) {
  void *q = realloc(p, n);
  if (!q) abort();
  return q;
}

#include "dns-tcp-aflnet.inc"

static void test_two_frames(void) {
  const unsigned char stream[] = {
    0, 12, 0x12, 0x34, 0x01, 0x00, 0, 1, 0, 0, 0, 0, 0, 0,
    0, 12, 0x56, 0x78, 0x85, 0x80, 0, 1, 0, 1, 0, 0, 0, 0
  };
  unsigned int n = 0;
  region_t *r = extract_requests_dns_tcp((unsigned char *)stream, sizeof(stream), &n);
  assert(n == 2 && r[0].start_byte == 0 && r[0].end_byte == 13);
  assert(r[1].start_byte == 14 && r[1].end_byte == 27);
  free(r);
  unsigned int *s = extract_response_codes_dns_tcp((unsigned char *)stream, sizeof(stream), &n);
  assert(n == 3 && s[0] == 0);
  assert(s[1] == 0xD3000000U); /* Query RD bit is intentionally ignored. */
  assert(s[2] == (0xD3000000U | 0x8400U)); /* QR and AA are server states. */
  free(s);
}

static void test_truncated_frame(void) {
  const unsigned char truncated[] = {0, 20, 0, 1, 0x81};
  unsigned int n = 0;
  region_t *r = extract_requests_dns_tcp((unsigned char *)truncated, sizeof(truncated), &n);
  assert(n == 1 && r[0].start_byte == 0 && r[0].end_byte == 4);
  free(r);
  unsigned int *s = extract_response_codes_dns_tcp((unsigned char *)truncated, sizeof(truncated), &n);
  assert(n == 2 && s[1] == 0xD3FFFFU);
  free(s);
}

int main(void) {
  test_two_frames();
  test_truncated_frame();
  puts("PASS: DNS/TCP length-prefix framing, multi-message response states, and truncation");
  return 0;
}
