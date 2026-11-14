#include <stdio.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static void append_text(unsigned char *buffer, size_t *used, const char *text)
{
	size_t length = strlen(text);
	memcpy(buffer + *used, text, length);
	*used += length;
}

static int fail(const char *message)
{
	fprintf(stderr, "SIP 解析器检查失败：%s\n", message);
	return 1;
}

int main(void)
{
	unsigned char requests[8192];
	unsigned char responses[4096];
	const char *body =
		"v=0\r\n"
		"o=fuzz 1 1 IN IP4 127.0.0.1\r\n"
		"s=Fuzz SIP\r\n"
		"c=IN IP4 127.0.0.1\r\n"
		"t=0 0\r\n"
		"m=audio 4000 RTP/AVP 0\r\n"
		"a=rtpmap:0 PCMU/8000\r\n"
		"x-body-text=BYE sip:fake@127.0.0.1 SIP/2.0\r\n";
	const char *response_body = "SIP/2.0 599 body-text\r\n";
	char header[512];
	size_t request_bytes = 0;
	size_t response_bytes = 0;
	unsigned int count = 0;
	unsigned int state_count = 0;
	region_t *regions;
	unsigned int *states;

	append_text(requests, &request_bytes,
		"OPTIONS sip:alice@127.0.0.1 SIP/2.0\r\n"
		"Via: SIP/2.0/TCP 127.0.0.1:5061;branch=z9hG4bK-options\r\n"
		"From: <sip:alice@127.0.0.1>;tag=options\r\n"
		"To: <sip:alice@127.0.0.1>\r\n"
		"Call-ID: options@127.0.0.1\r\n"
		"CSeq: 1 OPTIONS\r\n"
		"Content-Length: 0\r\n\r\n");
	append_text(requests, &request_bytes,
		"REGISTER sip:127.0.0.1 SIP/2.0\r\n"
		"Via: SIP/2.0/TCP 127.0.0.1:5061;branch=z9hG4bK-register\r\n"
		"From: <sip:alice@127.0.0.1>;tag=register\r\n"
		"To: <sip:alice@127.0.0.1>\r\n"
		"Call-ID: register@127.0.0.1\r\n"
		"CSeq: 1 REGISTER\r\n"
		"Contact: <sip:alice@127.0.0.1:5061;transport=tcp>\r\n"
		"Expires: 300\r\n"
		"Content-Length: 0\r\n\r\n");
	snprintf(header, sizeof(header),
		"INVITE sip:100@127.0.0.1 SIP/2.0\r\n"
		"Via: SIP/2.0/TCP 127.0.0.1:5061;branch=z9hG4bK-dialog\r\n"
		"From: <sip:alice@127.0.0.1>;tag=dialog\r\n"
		"To: <sip:100@127.0.0.1>\r\n"
		"Call-ID: dialog@127.0.0.1\r\n"
		"CSeq: 2 INVITE\r\n"
		"Contact: <sip:alice@127.0.0.1:5061;transport=tcp>\r\n"
		"Content-Type: application/sdp\r\n"
		"Content-Length: %lu\r\n\r\n",
		(unsigned long)strlen(body));
	append_text(requests, &request_bytes, header);
	append_text(requests, &request_bytes, body);
	append_text(requests, &request_bytes,
		"CANCEL sip:100@127.0.0.1 SIP/2.0\r\n"
		"Via: SIP/2.0/TCP 127.0.0.1:5061;branch=z9hG4bK-dialog\r\n"
		"From: <sip:alice@127.0.0.1>;tag=dialog\r\n"
		"To: <sip:100@127.0.0.1>\r\n"
		"Call-ID: dialog@127.0.0.1\r\n"
		"CSeq: 2 CANCEL\r\n"
		"Content-Length: 0\r\n\r\n");

	regions = extract_requests_sip(requests, (unsigned int)request_bytes, &count);
	if (count != 4U) {
		return fail("连续 OPTIONS、REGISTER、INVITE、CANCEL 未按消息边界切分");
	}
	if (regions[0].start_byte != 0 || regions[0].end_byte + 1 != regions[1].start_byte ||
	    regions[1].end_byte + 1 != regions[2].start_byte ||
	    regions[2].end_byte + 1 != regions[3].start_byte ||
	    (size_t)(regions[2].end_byte - regions[2].start_byte + 1) <= strlen(body)) {
		return fail("SIP 报文起止偏移错误，或正文中的伪请求造成了误切分");
	}
	ck_free(regions);

	regions = extract_requests_sip(requests, (unsigned int)request_bytes - 5U, &count);
	if (count != 4U || regions[3].start_byte <= regions[2].end_byte ||
	    regions[3].end_byte != (int)request_bytes - 6) {
		return fail("截断的 SIP 尾部没有作为独立区域保留");
	}
	ck_free(regions);

	{
		const char *bad =
			"OPTIONS sip:alice@127.0.0.1 SIP/2.0\r\n"
			"Via: SIP/2.0/TCP 127.0.0.1:5061;branch=z9hG4bK-bad\r\n"
			"Content-Length: 999999999999999999999999999999999999\r\n\r\n";
		regions = extract_requests_sip((unsigned char *)bad,
			(unsigned int)strlen(bad), &count);
		if (count != 1U || regions[0].start_byte != 0 ||
		    regions[0].end_byte != (int)strlen(bad) - 1) {
			return fail("非法超长 Content-Length 没有安全保留为一个尾部区域");
		}
		ck_free(regions);
	}

	append_text(responses, &response_bytes,
		"SIP/2.0 100 Trying\r\nContent-Length: 0\r\n\r\n"
		"SIP/2.0 200 OK\r\nContent-Type: text/plain\r\n");
	snprintf(header, sizeof(header), "Content-Length: %lu\r\n\r\n",
		(unsigned long)strlen(response_body));
	append_text(responses, &response_bytes, header);
	append_text(responses, &response_bytes, response_body);
	append_text(responses, &response_bytes,
		"SIP/2.0 487 Request Terminated\r\nContent-Length: 0\r\n\r\n");
	states = extract_response_codes_sip(responses, (unsigned int)response_bytes,
		&state_count);
	if (state_count != 4U || states[0] != 0U || states[1] != 100U ||
	    states[2] != 200U || states[3] != 487U) {
		return fail("响应状态解析错误，或正文中的伪状态码进入状态图");
	}
	ck_free(states);

	puts("通过：SIP 多消息、正文长度、截断尾部、非法长度和 100/200/487 状态映射");
	return 0;
}
