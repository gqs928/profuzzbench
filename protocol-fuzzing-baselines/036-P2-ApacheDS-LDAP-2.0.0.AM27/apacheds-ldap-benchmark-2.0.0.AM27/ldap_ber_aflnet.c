/* BER-framed LDAP request segmentation and response-state extraction for AFLNet. */
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

static void ldap_append_region(region_t **regions, unsigned int *count,
                               unsigned int start, unsigned int end) {
  *regions = (region_t *)ck_realloc(*regions, (*count + 1) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

static int ber_tlv(const unsigned char *buf, unsigned int limit,
                   unsigned int offset, unsigned char *tag_ref,
                   unsigned int *value_start_ref,
                   unsigned int *value_end_ref,
                   unsigned int *next_ref) {
  unsigned int len_octets = 1, value_len = 0, value_start, i;
  unsigned char first_len;
  if (!buf || offset >= limit || limit - offset < 2) return 0;
  *tag_ref = buf[offset];
  first_len = buf[offset + 1];
  if ((first_len & 0x80) == 0) {
    value_len = first_len;
  } else {
    unsigned int n = first_len & 0x7f;
    if (n == 0 || n > 4 || limit - offset < 2 + n) return 0;
    len_octets += n;
    for (i = 0; i < n; i++) value_len = (value_len << 8) | buf[offset + 2 + i];
  }
  value_start = offset + 1 + len_octets;
  if (value_start > limit || value_len > limit - value_start) return 0;
  *value_start_ref = value_start;
  *value_end_ref = value_start + value_len;
  *next_ref = value_start + value_len;
  return 1;
}

region_t *extract_requests_ldap(unsigned char *buf, unsigned int buf_size,
                                unsigned int *region_count_ref) {
  region_t *regions = NULL;
  unsigned int count = 0, offset = 0;
  if (!buf || !buf_size) { *region_count_ref = 0; return NULL; }
  while (offset < buf_size) {
    unsigned char tag = 0;
    unsigned int value_start = 0, value_end = 0, next = 0;
    if (buf[offset] != 0x30 ||
        !ber_tlv(buf, buf_size, offset, &tag, &value_start, &value_end, &next) ||
        tag != 0x30 || next <= offset) {
      ldap_append_region(&regions, &count, offset, buf_size - 1);
      break;
    }
    ldap_append_region(&regions, &count, offset, next - 1);
    offset = next;
  }
  *region_count_ref = count;
  return regions;
}

static unsigned int ldap_response_state(const unsigned char *buf,
                                        unsigned int start,
                                        unsigned int end) {
  unsigned char outer_tag, child_tag, op_tag, result_tag;
  unsigned int value_start, value_end, next, msgid_start, msgid_end;
  unsigned int op_start, op_end, op_next, result_start, result_end, result_next;
  unsigned int code = 0xff, i;
  if (!ber_tlv(buf, end, start, &outer_tag, &value_start, &value_end, &next) ||
      outer_tag != 0x30 || next != end) return 0x1fff;
  if (!ber_tlv(buf, value_end, value_start, &child_tag, &msgid_start, &msgid_end, &next) ||
      child_tag != 0x02 || next >= value_end) return 0x1ffe;
  if (!ber_tlv(buf, value_end, next, &op_tag, &op_start, &op_end, &op_next) ||
      op_next > value_end) return 0x1ffe;
  if (op_start < op_end &&
      ber_tlv(buf, op_end, op_start, &result_tag, &result_start, &result_end, &result_next) &&
      result_tag == 0x0a && result_end > result_start && result_end - result_start <= 4) {
    code = 0;
    for (i = result_start; i < result_end; i++) code = (code << 8) | buf[i];
  }
  return 0x10000u | ((unsigned int)op_tag << 8) | code;
}

unsigned int *extract_response_codes_ldap(unsigned char *buf,
                                          unsigned int buf_size,
                                          unsigned int *state_count_ref) {
  unsigned int *states = NULL, count = 0, offset = 0;
  states = (unsigned int *)ck_realloc(states, sizeof(unsigned int));
  states[count++] = 0;
  while (buf && offset < buf_size) {
    unsigned char tag = 0;
    unsigned int value_start = 0, value_end = 0, next = 0;
    if (buf[offset] != 0x30 ||
        !ber_tlv(buf, buf_size, offset, &tag, &value_start, &value_end, &next) ||
        tag != 0x30 || next <= offset) {
      states = (unsigned int *)ck_realloc(states, (count + 1) * sizeof(unsigned int));
      states[count++] = 0x1fff;
      break;
    }
    states = (unsigned int *)ck_realloc(states, (count + 1) * sizeof(unsigned int));
    states[count++] = ldap_response_state(buf, offset, next);
    offset = next;
  }
  *state_count_ref = count;
  return states;
}
