#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

region_t *extract_requests_imap(unsigned char *, unsigned int, unsigned int *);
unsigned int *extract_response_codes_imap(unsigned char *, unsigned int,
                                          unsigned int *);

static void test_request_framing(void)
{
  static unsigned char request[] =
      "A1 NOOP\r\n"
      "A2 APPEND INBOX {4}\r\n"
      "x\r\ny\r\n"
      "A3 LOGOUT\r\n";
  unsigned int count = 0;
  region_t *regions = extract_requests_imap(request, sizeof(request) - 1U, &count);

  assert(count == 3U);
  assert(regions[0].end_byte - regions[0].start_byte + 1 == 9);
  assert(regions[1].end_byte - regions[1].start_byte + 1 == 27);
  assert(regions[2].end_byte - regions[2].start_byte + 1 == 11);
  ck_free(regions);
}

static void test_partial_request(void)
{
  static unsigned char request[] = "A4 APPEND INBOX {9}\r\nabc";
  unsigned int count = 0;
  region_t *regions = extract_requests_imap(request, sizeof(request) - 1U, &count);

  assert(count == 1U);
  assert(regions[0].start_byte == 0);
  assert(regions[0].end_byte == (int)sizeof(request) - 2);
  ck_free(regions);
}

static void test_response_states_and_literal(void)
{
  static unsigned char response[] =
      "* OK Ready\r\n"
      "* 2 EXISTS\r\n"
      "* 1 FETCH (BODY[] {11}\r\n"
      "* OK fake\r\n"
      "A1 OK done\r\n";
  static const unsigned int expected[] = {0U, 1U, 9U, 11U, 20U};
  unsigned int count = 0;
  unsigned int *states = extract_response_codes_imap(
      response, sizeof(response) - 1U, &count);

  assert(count == sizeof(expected) / sizeof(expected[0]));
  for (unsigned int i = 0; i < count; ++i) assert(states[i] == expected[i]);
  ck_free(states);
}

int main(void)
{
  test_request_framing();
  test_partial_request();
  test_response_states_and_literal();
  puts("IMAP line/literal framing, partial-tail and response-state tests passed");
  return 0;
}
