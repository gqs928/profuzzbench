/* AFLNet adapter for iSCSI PDU framing and target response states. */
#include <limits.h>
#include <stdint.h>

#include "alloc-inl.h"
#include "aflnet.h"

#define ISCSI_BHS_SIZE 48U
#define ISCSI_MAX_PROFILE_PDU (1024U * 1024U)

static uint32_t iscsi_data_length(const unsigned char *buf)
{
  return ((uint32_t)buf[5] << 16) | ((uint32_t)buf[6] << 8) | (uint32_t)buf[7];
}

static int iscsi_pdu_size(const unsigned char *buf, unsigned int available,
                          unsigned int *size)
{
  uint64_t header_size;
  uint64_t data_size;
  uint64_t total;

  if (available < ISCSI_BHS_SIZE) return 0;
  header_size = ISCSI_BHS_SIZE + (uint64_t)buf[4] * 4U;
  data_size = iscsi_data_length(buf);
  total = header_size + data_size + ((4U - (data_size & 3U)) & 3U);
  if (total > UINT_MAX || total > ISCSI_MAX_PROFILE_PDU) return -1;
  *size = (unsigned int)total;
  return available >= *size ? 1 : 0;
}

static void add_region(region_t **regions, unsigned int *count,
                       unsigned int start, unsigned int end)
{
  *regions = (region_t *)ck_realloc(*regions, (*count + 1U) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

region_t *extract_requests_iscsi(unsigned char *buf, unsigned int buf_size,
                                 unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0;
  unsigned int offset = 0;

  while (offset < buf_size) {
    unsigned int pdu_size = 0;
    int parsed = iscsi_pdu_size(buf + offset, buf_size - offset, &pdu_size);
    if (parsed != 1) {
      /* Keep malformed or truncated bytes fuzzable as one final request. */
      add_region(&regions, &count, offset, buf_size - 1U);
      break;
    }
    add_region(&regions, &count, offset, offset + pdu_size - 1U);
    offset += pdu_size;
  }

  *region_count_ref = count;
  return regions;
}

static void add_state(unsigned int **states, unsigned int *count,
                      unsigned int state)
{
  *states = (unsigned int *)ck_realloc(*states, (*count + 1U) * sizeof(unsigned int));
  (*states)[*count] = state;
  (*count)++;
}

unsigned int *extract_response_codes_iscsi(unsigned char *buf,
                                           unsigned int buf_size,
                                           unsigned int *state_count_ref)
{
  unsigned int *states = NULL;
  unsigned int count = 0;
  unsigned int offset = 0;

  if (buf_size == 0) {
    *state_count_ref = 0;
    return NULL;
  }
  add_state(&states, &count, 0U);

  while (offset < buf_size) {
    unsigned int pdu_size = 0;
    unsigned int opcode;
    unsigned int status;
    unsigned int status_class = 0;
    unsigned int status_detail = 0;
    int parsed = iscsi_pdu_size(buf + offset, buf_size - offset, &pdu_size);

    if (parsed != 1) break;
    opcode = buf[offset] & 0x3fU;
    status = buf[offset + 3U];
    if (opcode == 0x23U) { /* Login Response: status class/detail. */
      status_class = buf[offset + 36U];
      status_detail = buf[offset + 37U];
    }
    add_state(&states, &count,
              (opcode << 24) | (status << 16) |
              (status_class << 8) | status_detail);
    offset += pdu_size;
  }

  *state_count_ref = count;
  return states;
}
