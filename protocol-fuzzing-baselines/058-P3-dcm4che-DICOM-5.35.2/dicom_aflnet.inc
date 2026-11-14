/* DICOM UL response states: preserve every complete PDU in a receive buffer,
 * and expose DIMSE command responses carried by command PDVs. */
#include <stddef.h>
#include <stdint.h>

static uint32_t dicom_read_u32be(const unsigned char *p) {
  return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
         ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static uint16_t dicom_read_u16le(const unsigned char *p) {
  return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static void dicom_add_response_state(unsigned int **states,
                                     unsigned int *count,
                                     unsigned int state) {
  *states = (unsigned int *)ck_realloc(
      *states, ((size_t)*count + 1U) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

/* Command Set elements always use Implicit VR Little Endian encoding. */
static int dicom_command_field(const unsigned char *buf, unsigned int size,
                              unsigned int *command) {
  unsigned int offset = 0;
  while (offset < size) {
    unsigned int element_length;
    if (size - offset < 8U) return -1;
    /* Command Set lengths are encoded little endian, unlike the UL PDU. */
    element_length = (uint32_t)buf[offset + 4U] |
                     ((uint32_t)buf[offset + 5U] << 8) |
                     ((uint32_t)buf[offset + 6U] << 16) |
                     ((uint32_t)buf[offset + 7U] << 24);
    if (element_length > size - offset - 8U) return -1;
    if (dicom_read_u16le(buf + offset) == 0U &&
        dicom_read_u16le(buf + offset + 2U) == 0x0100U) {
      if (element_length < 2U) return -1;
      *command = dicom_read_u16le(buf + offset + 8U);
      return 1;
    }
    offset += 8U + element_length;
  }
  return 0;
}

static int dicom_pdata_command(const unsigned char *body,
                               unsigned int body_size,
                               unsigned int *command) {
  unsigned int offset = 0;
  while (offset < body_size) {
    unsigned int item_length, command_value = 0;
    int found;
    if (body_size - offset < 4U) return -1;
    item_length = dicom_read_u32be(body + offset);
    if (item_length < 2U || item_length > body_size - offset - 4U)
      return -1;
    /* PDV data starts with context ID and message-control header. */
    if ((body[offset + 5U] & 0x01U) != 0U) {
      found = dicom_command_field(body + offset + 6U, item_length - 2U,
                                  &command_value);
      if (found < 0) return -1;
      if (found > 0) {
        *command = command_value;
        return 1;
      }
    }
    offset += 4U + item_length;
  }
  return 0;
}

unsigned int *extract_response_codes_dicom_profile(
    unsigned char *buf, unsigned int buf_size, unsigned int *state_count_ref) {
  unsigned int *states = NULL;
  unsigned int count = 0, offset = 0;
  *state_count_ref = 0;
  if (buf_size == 0U) return NULL;
  dicom_add_response_state(&states, &count, 0U);
  while (offset < buf_size) {
    unsigned int remaining = buf_size - offset;
    unsigned int pdu_type, pdu_length;
    if (remaining < 6U) {
      dicom_add_response_state(&states, &count, 0xD1FFF0U);
      break;
    }
    pdu_type = buf[offset];
    pdu_length = dicom_read_u32be(buf + offset + 2U);
    if (pdu_length > remaining - 6U) {
      dicom_add_response_state(&states, &count, 0xD1FFF1U);
      break;
    }
    if (pdu_type == 3U && pdu_length >= 4U) {
      const unsigned char *body = buf + offset + 6U;
      unsigned int reject = ((unsigned int)body[0] << 8) |
                            ((unsigned int)(body[1] & 0x0FU) << 4) |
                            (unsigned int)(body[2] & 0x0FU);
      dicom_add_response_state(&states, &count, 0xD30000U | reject);
    } else {
      dicom_add_response_state(&states, &count, 0xD10000U | pdu_type);
    }
    if (pdu_type == 4U) {
      unsigned int command = 0;
      int found = dicom_pdata_command(buf + offset + 6U, pdu_length,
                                      &command);
      if (found > 0)
        dicom_add_response_state(&states, &count, 0xD20000U | command);
      else if (found < 0)
        dicom_add_response_state(&states, &count, 0xD1FFF2U);
    }
    offset += 6U + pdu_length;
  }
  *state_count_ref = count;
  return states;
}
