/* AFLNet adapter for MQTT control packets over plaintext TCP.
 *
 * Request regions follow MQTT's fixed header and four-byte Remaining Length.
 * An incomplete or malformed tail stays one region so mutation cannot split a
 * packet payload into artificial requests. The adapter does not alter Mosquitto.
 */
#include <limits.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static void mqtt_append_region(region_t **regions, unsigned int *count,
                               unsigned int start, unsigned int end)
{
  *regions = (region_t *)ck_realloc(*regions, (*count + 1) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

/* Return 1 for a decoded length, 0 for a short input, and -1 for an invalid
 * five-byte/overflow encoding. MQTT Remaining Length uses at most four bytes. */
static int mqtt_decode_remaining_length(const unsigned char *buf,
                                        unsigned int size,
                                        unsigned int *length_bytes_ref,
                                        unsigned int *value_ref)
{
  unsigned int i, multiplier = 1, value = 0;

  for (i = 0; i < 4; i++) {
    unsigned int digit;
    if (i + 1 >= size) return 0;
    digit = buf[i + 1] & 0x7fU;
    if (digit && multiplier > UINT_MAX / digit) return -1;
    if (value > UINT_MAX - digit * multiplier) return -1;
    value += digit * multiplier;
    if ((buf[i + 1] & 0x80U) == 0) {
      *length_bytes_ref = i + 1;
      *value_ref = value;
      return 1;
    }
    multiplier *= 128U;
  }
  return -1;
}

region_t *extract_requests_mqtt(unsigned char *buf, unsigned int buf_size,
                                unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0, start = 0;

  if (!buf || !buf_size) {
    *region_count_ref = 0;
    return NULL;
  }

  while (start < buf_size) {
    unsigned int length_bytes = 0, remaining = 0, header_size, packet_size;
    int decoded = mqtt_decode_remaining_length(buf + start,
                                               buf_size - start,
                                               &length_bytes, &remaining);
    if (decoded <= 0) {
      mqtt_append_region(&regions, &count, start, buf_size - 1);
      break;
    }

    header_size = 1U + length_bytes;
    if (remaining > UINT_MAX - header_size) {
      mqtt_append_region(&regions, &count, start, buf_size - 1);
      break;
    }
    packet_size = header_size + remaining;
    if (packet_size > buf_size - start) {
      mqtt_append_region(&regions, &count, start, buf_size - 1);
      break;
    }

    mqtt_append_region(&regions, &count, start, start + packet_size - 1);
    start += packet_size;
  }

  *region_count_ref = count;
  return regions;
}

static unsigned int mqtt_packet_state(const unsigned char *buf,
                                      unsigned int start,
                                      unsigned int length_bytes,
                                      unsigned int remaining)
{
  unsigned int type = (buf[start] >> 4) & 0x0fU;

  /* Keep CONNACK failures distinct; all other server packet types have stable
   * IDs across MQTT 3.1.1 and 5.0, whose optional properties change packet size. */
  if (type == 2 && remaining >= 2)
    return 2000U + buf[start + 1 + length_bytes + 1];
  if (type >= 2 && type <= 15)
    return 100U + type;
  return 199U;
}

unsigned int *extract_response_codes_mqtt(unsigned char *buf,
                                          unsigned int buf_size,
                                          unsigned int *state_count_ref)
{
  unsigned int *states, count = 1, cursor = 0;

  states = (unsigned int *)ck_alloc(sizeof(unsigned int));
  states[0] = 0;
  if (!buf || !buf_size) {
    *state_count_ref = count;
    return states;
  }

  while (cursor < buf_size) {
    unsigned int length_bytes = 0, remaining = 0, packet_size;
    int decoded = mqtt_decode_remaining_length(buf + cursor,
                                               buf_size - cursor,
                                               &length_bytes, &remaining);
    if (decoded <= 0 || remaining > UINT_MAX - 1U - length_bytes) break;
    packet_size = 1U + length_bytes + remaining;
    if (packet_size > buf_size - cursor) break;

    states = (unsigned int *)ck_realloc(states, (count + 1) * sizeof(unsigned int));
    states[count++] = mqtt_packet_state(buf, cursor, length_bytes, remaining);
    cursor += packet_size;
  }

  *state_count_ref = count;
  return states;
}
