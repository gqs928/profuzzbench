#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

region_t *extract_requests_iscsi(unsigned char *, unsigned int, unsigned int *);
unsigned int *extract_response_codes_iscsi(unsigned char *, unsigned int,
                                           unsigned int *);

static void require(int ok, const char *message)
{
  if (!ok) {
    fprintf(stderr, "FAIL: %s\n", message);
    exit(1);
  }
}

static void make_pdu(unsigned char *p, unsigned char opcode,
                     const unsigned char *data, unsigned int length)
{
  memset(p, 0, 48U + ((length + 3U) & ~3U));
  p[0] = opcode;
  p[5] = (unsigned char)(length >> 16);
  p[6] = (unsigned char)(length >> 8);
  p[7] = (unsigned char)length;
  if (length) memcpy(p + 48, data, length);
}

int main(void)
{
  static const unsigned char text[] = {'A', 'B', 'C'};
  unsigned char requests[48U + 4U + 48U];
  unsigned char truncated[52];
  unsigned char responses[96];
  region_t *regions;
  unsigned int *states;
  unsigned int count = 0;
  unsigned int state_count = 0;

  make_pdu(requests, 0x43U, text, sizeof(text));
  make_pdu(requests + 52U, 0x01U, NULL, 0U);
  regions = extract_requests_iscsi(requests, sizeof(requests), &count);
  require(count == 2U, "two binary PDUs split by BHS data length and padding");
  require(regions[0].start_byte == 0 && regions[0].end_byte == 51,
          "first request includes four-byte data padding");
  require(regions[1].start_byte == 52 && regions[1].end_byte == 99,
          "second request starts at next BHS");
  ck_free(regions);

  make_pdu(truncated, 0x43U, text, sizeof(text));
  regions = extract_requests_iscsi(truncated, sizeof(truncated) - 1U, &count);
  require(count == 1U && regions[0].start_byte == 0 && regions[0].end_byte == 50,
          "truncated data segment remains a fuzzable request");
  ck_free(regions);

  make_pdu(responses, 0x23U, NULL, 0U);
  responses[36] = 0;
  responses[37] = 0;
  make_pdu(responses + 48U, 0x21U, NULL, 0U);
  responses[51] = 2;
  states = extract_response_codes_iscsi(responses, sizeof(responses), &state_count);
  require(state_count == 3U && states[0] == 0U,
          "state sequence has the initial state and both response PDUs");
  require(states[1] == (0x23U << 24), "login success maps to a distinct state");
  require(states[2] == ((0x21U << 24) | (2U << 16)),
          "SCSI status maps to a distinct response state");
  ck_free(states);

  puts("PASS: iSCSI BHS framing, padding, truncation, login and SCSI response states");
  return 0;
}
