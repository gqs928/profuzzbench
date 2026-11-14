#include <stdio.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

static int fail(const char *message)
{
  fprintf(stderr, "FAIL: %s\n", message);
  return 1;
}

int main(void)
{
  unsigned char request[] =
      "<stream:stream to='localhost' xmlns='jabber:client' "
      "xmlns:stream='http://etherx.jabber.org/streams'>"
      "<iq type='get' id='d'><query xmlns='urn:test'/></iq>"
      "<presence/><message><body>hi</body></message></stream:stream>";
  unsigned char response[] =
      "<stream:stream id='random'><stream:features><starttls/>"
      "<mechanisms><mechanism>PLAIN</mechanism></mechanisms>"
      "</stream:features><iq type='result' id='random'/>";
  unsigned int request_count = 0, state_count = 0, i;
  region_t *regions = extract_requests_xmpp(request, sizeof(request) - 1,
                                             &request_count);
  unsigned int *states = extract_response_codes_xmpp(
      response, sizeof(response) - 1, &state_count);
  const unsigned int expected[] = {0, 1001, 1002, 1003, 1005, 1006, 1012};

  if (!regions || request_count != 5) return fail("top-level XML stanza segmentation");
  if (regions[0].end_byte < regions[0].start_byte ||
      regions[1].end_byte < regions[1].start_byte ||
      regions[2].end_byte < regions[2].start_byte ||
      regions[3].end_byte < regions[3].start_byte ||
      regions[4].end_byte < regions[4].start_byte)
    return fail("invalid XMPP request region bounds");
  if (!states || state_count != sizeof(expected) / sizeof(expected[0]))
    return fail("XMPP response-state count");
  for (i = 0; i < state_count; i++)
    if (states[i] != expected[i]) return fail("stable XMPP response states");

  ck_free(regions);
  ck_free(states);
  puts("PASS: XMPP stream opener, nested stanzas, quoted attributes, and stable response states.");
  return 0;
}
