#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"
region_t *extract_requests_stomp(unsigned char *, unsigned int, unsigned int *);
unsigned int *extract_response_codes_stomp(unsigned char *, unsigned int, unsigned int *);
int main(void) {
  unsigned char req[] = "CONNECT\naccept-version:1.2\n\n\0SEND\ndestination:/q\n\nX\0TAIL";
  unsigned char rsp[] = "CONNECTED\nversion:1.2\n\n\0\nRECEIPT\nreceipt-id:r\n\n\0MESSAGE\ndestination:/q\n\nX\0ERROR\nmessage:oops\n\n\0";
  unsigned int n = 0, ns = 0;
  region_t *r = extract_requests_stomp(req, sizeof(req)-1, &n);
  assert(n == 3 && r[0].start_byte == 0 && req[r[0].end_byte] == 0);
  assert(req[r[1].start_byte] == 'S' && req[r[2].start_byte] == 'T');
  unsigned int *s = extract_response_codes_stomp(rsp, sizeof(rsp)-1, &ns);
  assert(ns == 5 && s[1] == 100 && s[2] == 102 && s[3] == 101 && s[4] == 199);
  ck_free(r); ck_free(s); return 0;
}
