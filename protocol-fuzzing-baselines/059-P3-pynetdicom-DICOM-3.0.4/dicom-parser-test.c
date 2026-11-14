#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define ck_realloc(ptr, size) realloc((ptr), (size))
#include "dicom_aflnet.inc"

static void test_complete_exchange(void) {
  /* AC, C-ECHO-RSP inside P-DATA-TF, then A-RELEASE-RP. */
  unsigned char response[] = {
      0x02, 0, 0, 0, 0, 0,
      0x04, 0, 0, 0, 0, 16,
      0, 0, 0, 12, 1, 3,
      0, 0, 0, 1, 2, 0, 0, 0, 0x30, 0x80,
      0x06, 0, 0, 0, 0, 4, 0, 0, 0, 0};
  unsigned int count = 0;
  unsigned int *states = extract_response_codes_dicom_profile(
      response, (unsigned int)sizeof(response), &count);
  assert(count == 5U);
  assert(states[0] == 0U);
  assert(states[1] == 0xD10002U);
  assert(states[2] == 0xD10004U);
  assert(states[3] == 0xD28030U);
  assert(states[4] == 0xD10006U);
  free(states);
}

static void test_association_reject_state(void) {
  unsigned char response[] = {0x03, 0, 0, 0, 0, 4, 2, 1, 7, 0};
  unsigned int count = 0;
  unsigned int *states = extract_response_codes_dicom_profile(
      response, (unsigned int)sizeof(response), &count);
  assert(count == 2U);
  assert(states[1] == (0xD30000U | 0x217U));
  free(states);
}

static void test_truncated_pdu_state(void) {
  unsigned char response[] = {0x02, 0, 0, 0, 0, 2, 0};
  unsigned int count = 0;
  unsigned int *states = extract_response_codes_dicom_profile(
      response, (unsigned int)sizeof(response), &count);
  assert(count == 2U);
  assert(states[1] == 0xD1FFF1U);
  free(states);
}

int main(void) {
  test_complete_exchange();
  test_association_reject_state();
  test_truncated_pdu_state();
  puts("PASS: DICOM multi-PDU response framing, DIMSE command state, and malformed lengths");
  return 0;
}
