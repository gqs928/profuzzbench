#include <stdint.h>

#include "alloc-inl.h"
#include "aflnet.h"

#define RPC_RECORD_MAX (16U * 1024U * 1024U)
#define NFS_STATE_BASE 0x10000U
#define RPC_ACCEPT_STATE_BASE 0x20000U
#define RPC_DENIED_STATE_BASE 0x30000U
#define MALFORMED_STATE 0x40000U

/* 以网络序读取一个 32 位整数，避免未对齐访问。 */
static uint32_t nfs_read_u32(const unsigned char *data)
{
	return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) |
	       ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

/* 将一段 RPC record 保存为 AFLNet 可独立变异的请求区域。 */
static void nfs_append_region(region_t **regions, unsigned int *count,
			      unsigned int start, unsigned int end)
{
	*regions = (region_t *)ck_realloc(*regions,
					   (*count + 1U) * sizeof(region_t));
	(*regions)[*count].start_byte = (int)start;
	(*regions)[*count].end_byte = (int)end;
	(*regions)[*count].modifiable = 1;
	(*regions)[*count].state_sequence = NULL;
	(*regions)[*count].state_count = 0;
	(*count)++;
}

/* 按 ONC RPC record marker 切分请求，并将多片段 record 合并为一个请求。 */
region_t *extract_requests_nfs(unsigned char *buf, unsigned int buf_size,
			       unsigned int *region_count_ref)
{
	region_t *regions = NULL;
	unsigned int count = 0U;
	unsigned int cursor = 0U;

	if (!region_count_ref)
		return NULL;
	if (!buf || buf_size == 0U) {
		*region_count_ref = 0U;
		return NULL;
	}

	while (cursor < buf_size) {
		unsigned int record_start = cursor;
		int complete = 0;

		while (!complete) {
			uint32_t marker;
			uint32_t fragment_len;
			unsigned int remaining = buf_size - cursor;

			if (remaining < 4U) {
				nfs_append_region(&regions, &count, record_start,
						  buf_size - 1U);
				cursor = buf_size;
				break;
			}

			marker = nfs_read_u32(buf + cursor);
			fragment_len = marker & 0x7fffffffU;
			cursor += 4U;
			if (fragment_len > RPC_RECORD_MAX ||
			    fragment_len > buf_size - cursor) {
				nfs_append_region(&regions, &count, record_start,
						  buf_size - 1U);
				cursor = buf_size;
				break;
			}

			cursor += fragment_len;
			complete = (marker & 0x80000000U) != 0U;
			if (complete)
				nfs_append_region(&regions, &count, record_start,
						  cursor - 1U);
		}
	}

	*region_count_ref = count;
	return regions;
}

/* 把 NFSv3 返回码放入独立状态空间，保留协议原始状态值。 */
static unsigned int nfs_status_state(uint32_t status)
{
	return NFS_STATE_BASE | status;
}

/* 将一个 ONC RPC 回复映射为 RPC 层错误或 NFSv3 业务状态。 */
static unsigned int nfs_response_state(const unsigned char *record,
				       unsigned int record_len)
{
	uint32_t message_type;
	uint32_t reply_stat;
	uint32_t verifier_len;
	uint32_t accept_stat;
	unsigned int offset;
	unsigned int padded_verifier_len;

	if (record_len < 12U)
		return MALFORMED_STATE;

	message_type = nfs_read_u32(record + 4U);
	reply_stat = nfs_read_u32(record + 8U);
	if (message_type != 1U)
		return MALFORMED_STATE;

	if (reply_stat == 1U) {
		if (record_len < 16U)
			return MALFORMED_STATE;
		return RPC_DENIED_STATE_BASE | nfs_read_u32(record + 12U);
	}
	if (reply_stat != 0U || record_len < 24U)
		return MALFORMED_STATE;

	verifier_len = nfs_read_u32(record + 16U);
	if (verifier_len > RPC_RECORD_MAX)
		return MALFORMED_STATE;
	padded_verifier_len = (verifier_len + 3U) & ~3U;
	if (padded_verifier_len > record_len - 24U)
		return MALFORMED_STATE;

	offset = 20U + padded_verifier_len;
	if (offset + 4U > record_len)
		return MALFORMED_STATE;
	accept_stat = nfs_read_u32(record + offset);
	if (accept_stat != 0U)
		return RPC_ACCEPT_STATE_BASE | accept_stat;

	offset += 4U;
	if (offset + 4U > record_len)
		return MALFORMED_STATE;
	return nfs_status_state(nfs_read_u32(record + offset));
}

/* 逐条读取带 record marker 的回复，并记录 NFSv3 状态序列。 */
unsigned int *extract_response_codes_nfs(unsigned char *buf,
					 unsigned int buf_size,
					 unsigned int *state_count_ref)
{
	unsigned int *states;
	unsigned int count = 1U;
	unsigned int cursor = 0U;

	if (!state_count_ref)
		return NULL;
	states = (unsigned int *)ck_alloc(sizeof(unsigned int));
	states[0] = 0U;
	if (!buf || buf_size == 0U) {
		*state_count_ref = count;
		return states;
	}

	while (cursor < buf_size) {
		unsigned int record_start = cursor;
		unsigned int record_end;
		int complete = 0;

		while (!complete) {
			uint32_t marker;
			uint32_t fragment_len;

			if (buf_size - cursor < 4U) {
				cursor = buf_size;
				break;
			}
			marker = nfs_read_u32(buf + cursor);
			fragment_len = marker & 0x7fffffffU;
			cursor += 4U;
			if (fragment_len > RPC_RECORD_MAX ||
			    fragment_len > buf_size - cursor) {
				cursor = buf_size;
				break;
			}
			cursor += fragment_len;
			complete = (marker & 0x80000000U) != 0U;
		}

		if (!complete) {
			states = (unsigned int *)ck_realloc(
				states, (count + 1U) * sizeof(unsigned int));
			states[count++] = MALFORMED_STATE;
			break;
		}

		record_end = cursor;
		states = (unsigned int *)ck_realloc(
			states, (count + 1U) * sizeof(unsigned int));
		states[count++] = nfs_response_state(buf + record_start + 4U,
						     record_end - record_start - 4U);
	}

	*state_count_ref = count;
	return states;
}
