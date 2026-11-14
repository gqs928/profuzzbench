#include <stdio.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

#define TEST_PACKET_SIZE 20U

static void make_packet(unsigned char *packet, unsigned char code,
			unsigned char identifier)
{
	memset(packet, 0, TEST_PACKET_SIZE);
	packet[0] = code;
	packet[1] = identifier;
	packet[2] = 0;
	packet[3] = TEST_PACKET_SIZE;
}

static int fail(char const *message)
{
	fprintf(stderr, "协议解析器检查失败：%s\n", message);
	return 1;
}

int main(void)
{
	unsigned char input[TEST_PACKET_SIZE * 2U + 3U];
	unsigned int count = 0U;
	region_t *regions;
	unsigned int state_count = 0U;
	unsigned int *states;

	make_packet(input, 1U, 1U);
	make_packet(input + TEST_PACKET_SIZE, 4U, 2U);
	regions = extract_requests_radius(input, TEST_PACKET_SIZE * 2U, &count);
	if (count != 2U || regions[0].start_byte != 0 ||
	    regions[0].end_byte != (int)TEST_PACKET_SIZE - 1 ||
	    regions[1].start_byte != (int)TEST_PACKET_SIZE ||
	    regions[1].end_byte != (int)(TEST_PACKET_SIZE * 2U) - 1)
		return fail("连续 RADIUS 报文没有按 Length 字段切分");
	ck_free(regions);

	regions = extract_requests_radius(input, TEST_PACKET_SIZE + 3U, &count);
	if (count != 2U || regions[1].start_byte != (int)TEST_PACKET_SIZE ||
	    regions[1].end_byte != (int)(TEST_PACKET_SIZE + 2U))
		return fail("截断报文尾部没有保留为独立请求");
	ck_free(regions);

	input[2] = 0U;
	input[3] = 19U;
	regions = extract_requests_radius(input, TEST_PACKET_SIZE, &count);
	if (count != 1U || regions[0].start_byte != 0 ||
	    regions[0].end_byte != (int)TEST_PACKET_SIZE - 1)
		return fail("非法短长度报文没有保留为请求");
	ck_free(regions);

	make_packet(input, 2U, 1U);
	make_packet(input + TEST_PACKET_SIZE, 3U, 2U);
	states = extract_response_codes_radius(input, TEST_PACKET_SIZE * 2U,
					       &state_count);
	if (state_count != 3U || states[0] != 0U || states[1] != 2U ||
	    states[2] != 3U)
		return fail("Access-Accept 和 Access-Reject 状态映射错误");
	ck_free(states);

	make_packet(input, 5U, 3U);
	states = extract_response_codes_radius(input, TEST_PACKET_SIZE, &state_count);
	if (state_count != 2U || states[1] != 5U)
		return fail("Accounting-Response 状态映射错误");
	ck_free(states);

	puts("通过：合法多包、截断尾部、非法长度、认证与记账状态");
	return 0;
}
