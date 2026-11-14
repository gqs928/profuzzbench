#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static void put_u32(unsigned char *out, uint32_t value)
{
	out[0] = (unsigned char)(value >> 24);
	out[1] = (unsigned char)(value >> 16);
	out[2] = (unsigned char)(value >> 8);
	out[3] = (unsigned char)value;
}

static int fail(const char *message)
{
	fprintf(stderr, "NFS 解析器检查失败：%s\n", message);
	return 1;
}

static unsigned int make_reply(unsigned char *out, uint32_t status)
{
	put_u32(out, 0x8000001cU);
	put_u32(out + 4, 7U);
	put_u32(out + 8, 1U);
	put_u32(out + 12, 0U);
	put_u32(out + 16, 0U);
	put_u32(out + 20, 0U);
	put_u32(out + 24, 0U);
	put_u32(out + 28, status);
	return 32U;
}

int main(void)
{
	unsigned char requests[32];
	unsigned char replies[64];
	unsigned int count = 0U;
	unsigned int state_count = 0U;
	region_t *regions;
	unsigned int *states;

	put_u32(requests, 0x00000004U);
	memcpy(requests + 4, "abcd", 4);
	put_u32(requests + 8, 0x80000003U);
	memcpy(requests + 12, "xyz", 3);
	put_u32(requests + 15, 0x80000000U);
	regions = extract_requests_nfs(requests, 19U, &count);
	if (count != 2U || regions[0].start_byte != 0 ||
	    regions[0].end_byte != 14 || regions[1].start_byte != 15 ||
	    regions[1].end_byte != 18)
		return fail("连续 record 与多片段 record 边界不正确");
	ck_free(regions);

	regions = extract_requests_nfs(requests, 17U, &count);
	if (count != 2U || regions[1].start_byte != 15 ||
	    regions[1].end_byte != 16)
		return fail("截断的 record marker 尾部没有保留");
	ck_free(regions);

	put_u32(requests, 0x80000010U);
	regions = extract_requests_nfs(requests, 8U, &count);
	if (count != 1U || regions[0].start_byte != 0 ||
	    regions[0].end_byte != 7)
		return fail("截断的 RPC record 没有作为异常请求保留");
	ck_free(regions);

	make_reply(replies, 0U);
	make_reply(replies + 32U, 2U);
	states = extract_response_codes_nfs(replies, 64U, &state_count);
	if (state_count != 3U || states[0] != 0U ||
	    states[1] != 0x10000U || states[2] != 0x10002U)
		return fail("NFS3_OK 与 NFS3ERR_NOENT 状态映射不正确");
	ck_free(states);

	put_u32(replies, 0x80000010U);
	put_u32(replies + 4U, 9U);
	put_u32(replies + 8U, 1U);
	put_u32(replies + 12U, 1U);
	put_u32(replies + 16U, 1U);
	states = extract_response_codes_nfs(replies, 20U, &state_count);
	if (state_count != 2U || states[1] != 0x30001U)
		return fail("RPC_MSG_DENIED 状态映射不正确");
	ck_free(states);

	puts("通过：ONC RPC 多包/多片段边界、截断尾部、NFSv3 与 RPC 错误状态");
	return 0;
}
