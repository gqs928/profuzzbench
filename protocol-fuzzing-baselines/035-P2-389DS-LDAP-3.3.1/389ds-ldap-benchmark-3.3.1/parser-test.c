#include <assert.h>
#include <stdlib.h>
#include "alloc-inl.h"
#include "aflnet.h"

region_t *extract_requests_ldap(unsigned char *, unsigned int, unsigned int *);
unsigned int *extract_response_codes_ldap(unsigned char *, unsigned int, unsigned int *);

int main(void) {
  unsigned char req[] = {
    0x30,0x0c,0x02,0x01,0x01,0x60,0x07,0x02,0x01,0x03,0x04,0x00,0x80,0x00,
    0x30,0x05,0x02,0x01,0x02,0x42,0x00,
    0x30,0x80
  };
  unsigned char rsp[] = {
    0x30,0x0c,0x02,0x01,0x01,0x61,0x07,0x0a,0x01,0x00,0x04,0x00,0x04,0x00,
    0x30,0x0c,0x02,0x01,0x02,0x65,0x07,0x0a,0x01,0x20,0x04,0x00,0x04,0x00
  };
  unsigned int n = 0, ns = 0;
  region_t *r = extract_requests_ldap(req, sizeof(req), &n);
  assert(n == 3);
  assert(r[0].start_byte == 0 && r[0].end_byte == 13);
  assert(r[1].start_byte == 14 && r[1].end_byte == 20);
  assert(r[2].start_byte == 21 && r[2].end_byte == 22);
  unsigned int *s = extract_response_codes_ldap(rsp, sizeof(rsp), &ns);
  assert(ns == 3 && s[0] == 0);
  assert(s[1] == (0x10000u | (0x61u << 8) | 0));
  assert(s[2] == (0x10000u | (0x65u << 8) | 32));
  ck_free(r); ck_free(s); return 0;
}
