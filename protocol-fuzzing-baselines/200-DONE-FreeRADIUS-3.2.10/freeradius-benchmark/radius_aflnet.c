#include <limits.h>
#include <stdint.h>

#include "alloc-inl.h"
#include "aflnet.h"

#define RADIUS_HEADER_SIZE 20U
#define RADIUS_MAX_PACKET_SIZE 65535U

/* 将无法按长度完整解析的数据尾部保留为单独请求，确保畸形输入仍能到达服务端。 */
static void radius_append_region(region_t **regions, unsigned int *count,
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

/* 从 RADIUS 头部的网络序 Length 字段切分 TCP 字节流中的连续报文。 */
region_t *extract_requests_radius(unsigned char *buf, unsigned int buf_size,
				  unsigned int *region_count_ref)
{
	region_t *regions = NULL;
	unsigned int count = 0, cursor = 0;

	if (!region_count_ref) return NULL;
	if (!buf || !buf_size) {
		*region_count_ref = 0;
		return NULL;
	}

	while (cursor < buf_size) {
		unsigned int remaining = buf_size - cursor;
		unsigned int packet_size;

		if (remaining < 4U) {
			radius_append_region(&regions, &count, cursor, buf_size - 1U);
			break;
		}
		packet_size = ((unsigned int)buf[cursor + 2U] << 8) |
			      (unsigned int)buf[cursor + 3U];
		if (packet_size < RADIUS_HEADER_SIZE ||
		    packet_size > RADIUS_MAX_PACKET_SIZE || packet_size > remaining ||
		    packet_size > (unsigned int)INT_MAX ||
		    cursor > (unsigned int)INT_MAX - packet_size) {
			radius_append_region(&regions, &count, cursor, buf_size - 1U);
			break;
		}
		radius_append_region(&regions, &count, cursor,
				     cursor + packet_size - 1U);
		cursor += packet_size;
	}

	*region_count_ref = count;
	return regions;
}

/* 把认证、挑战、拒绝和记账响应映射为 RADIUS Code，供状态图识别业务阶段。 */
static unsigned int radius_response_state(unsigned char code)
{
	switch (code) {
	case 2U:  return 2U;   /* Access-Accept */
	case 3U:  return 3U;   /* Access-Reject */
	case 5U:  return 5U;   /* Accounting-Response */
	case 11U: return 11U;  /* Access-Challenge */
	case 12U: return 12U;  /* Status-Server */
	case 13U: return 13U;  /* Status-Client */
	case 41U: return 41U;  /* Disconnect-ACK */
	case 42U: return 42U;  /* Disconnect-NAK */
	case 44U: return 44U;  /* CoA-ACK */
	case 45U: return 45U;  /* CoA-NAK */
	default:  return 255U; /* 未识别或异常响应 */
	}
}

unsigned int *extract_response_codes_radius(unsigned char *buf,
						    unsigned int buf_size,
						    unsigned int *state_count_ref)
{
	unsigned int *states, count = 1U, cursor = 0U;

	if (!state_count_ref) return NULL;
	states = (unsigned int *)ck_alloc(sizeof(unsigned int));
	states[0] = 0U;
	if (!buf || !buf_size) {
		*state_count_ref = count;
		return states;
	}

	while (buf_size - cursor >= RADIUS_HEADER_SIZE) {
		unsigned int packet_size = ((unsigned int)buf[cursor + 2U] << 8) |
					   (unsigned int)buf[cursor + 3U];
		if (packet_size < RADIUS_HEADER_SIZE || packet_size > buf_size - cursor)
			break;
		states = (unsigned int *)ck_realloc(states,
						    (count + 1U) * sizeof(unsigned int));
		states[count++] = radius_response_state(buf[cursor]);
		cursor += packet_size;
	}

	*state_count_ref = count;
	return states;
}
