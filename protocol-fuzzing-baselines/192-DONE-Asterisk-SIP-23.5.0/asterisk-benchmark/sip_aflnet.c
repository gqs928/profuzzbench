/* SIP/TCP 报文边界与响应状态解析器，供 AFLNet 使用。 */
#include <ctype.h>
#include <limits.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

/* 查找 SIP 头部结束位置，并返回正文起点。 */
static int sip_find_header_end(const unsigned char *buf, size_t start,
			       size_t limit, size_t *body_start)
{
	size_t i;

	for (i = start; i < limit; ++i) {
		if (i + 3 < limit && buf[i] == '\r' && buf[i + 1] == '\n' &&
		    buf[i + 2] == '\r' && buf[i + 3] == '\n') {
			*body_start = i + 4;
			return 1;
		}
		if (i + 1 < limit && buf[i] == '\n' && buf[i + 1] == '\n') {
			*body_start = i + 2;
			return 1;
		}
	}
	return 0;
}

/* 比较 ASCII 头字段名，避免大小写差异影响 Content-Length 识别。 */
static int sip_header_name_equal(const unsigned char *buf, size_t start,
				 size_t end, const char *name)
{
	size_t i;
	size_t name_len = strlen(name);

	if (end - start != name_len) {
		return 0;
	}
	for (i = 0; i < name_len; ++i) {
		if (tolower(buf[start + i]) != tolower((unsigned char)name[i])) {
			return 0;
		}
	}
	return 1;
}

/* 解析 Content-Length/紧凑字段 l；缺失时按无正文处理，冲突时拒绝切分。 */
static int sip_content_length(const unsigned char *buf, size_t start,
			      size_t body_start, size_t *content_length)
{
	size_t line_start = start;
	size_t line_end;
	size_t header_end;
	size_t parsed_length = 0;
	int found = 0;

	while (line_start < body_start && buf[line_start] != '\n') {
		++line_start;
	}
	if (line_start == body_start) {
		return 0;
	}
	++line_start;
	header_end = body_start >= 2 ? body_start - 2 : body_start;

	while (line_start < header_end) {
		size_t colon;
		size_t value_start;
		size_t value_end;
		size_t value = 0;
		size_t i;
		int is_length;

		line_end = line_start;
		while (line_end < header_end && buf[line_end] != '\n') {
			++line_end;
		}
		if (line_end > line_start && buf[line_end - 1] == '\r') {
			--line_end;
		}
		colon = line_start;
		while (colon < line_end && buf[colon] != ':') {
			++colon;
		}
		is_length = colon < line_end &&
			(sip_header_name_equal(buf, line_start, colon, "content-length") ||
			 sip_header_name_equal(buf, line_start, colon, "l"));
		if (is_length) {
			value_start = colon + 1;
			value_end = line_end;
			while (value_start < value_end &&
			       (buf[value_start] == ' ' || buf[value_start] == '\t')) {
				++value_start;
			}
			while (value_end > value_start &&
			       (buf[value_end - 1] == ' ' || buf[value_end - 1] == '\t')) {
				--value_end;
			}
			if (value_start == value_end) {
				return 0;
			}
			for (i = value_start; i < value_end; ++i) {
				if (!isdigit(buf[i]) || value > (SIZE_MAX - 9) / 10) {
					return 0;
				}
				value = value * 10 + (size_t)(buf[i] - '0');
			}
			if (found && value != parsed_length) {
				return 0;
			}
			parsed_length = value;
			found = 1;
		}
		line_start = line_end;
		while (line_start < header_end && buf[line_start] != '\n') {
			++line_start;
		}
		if (line_start < header_end) {
			++line_start;
		}
	}
	*content_length = found ? parsed_length : 0;
	return 1;
}

/* 计算一个 SIP 消息总长；不完整或长度冲突时返回 0。 */
static size_t sip_message_extent(const unsigned char *buf, size_t start,
				 size_t limit)
{
	size_t body_start;
	size_t content_length;

	if (!sip_find_header_end(buf, start, limit, &body_start) ||
	    !sip_content_length(buf, start, body_start, &content_length) ||
	    content_length > limit - body_start) {
		return 0;
	}
	return body_start - start + content_length;
}

/* 把一个完整报文或未完成尾部登记为 AFLNet 可变异区域。 */
static region_t *sip_append_region(region_t *regions, unsigned int *count,
				   size_t start, size_t end)
{
	if (*count == 0) {
		regions = (region_t *)ck_alloc(sizeof(region_t));
	} else {
		regions = (region_t *)ck_realloc(regions,
			(*count + 1) * sizeof(region_t));
	}
	regions[*count].start_byte = (int)start;
	regions[*count].end_byte = (int)end;
	regions[*count].state_sequence = NULL;
	regions[*count].state_count = 0;
	++*count;
	return regions;
}

/* 切分 TCP 流时按头部边界和 Content-Length 前进，正文中的伪请求不拆包。 */
region_t *sip_aflnet_extract_requests(unsigned char *buf, unsigned int buf_size,
				      unsigned int *region_count_ref)
{
	region_t *regions = NULL;
	unsigned int region_count = 0;
	size_t cursor = 0;
	size_t total = buf_size;

	while (cursor < total) {
		size_t extent = sip_message_extent(buf, cursor, total);
		if (extent == 0) {
			regions = sip_append_region(regions, &region_count, cursor,
						    total - 1);
			break;
		}
		regions = sip_append_region(regions, &region_count, cursor,
					    cursor + extent - 1);
		cursor += extent;
	}
	*region_count_ref = region_count;
	return regions;
}

/* 从 SIP/2.0 状态行提取三位响应码。 */
static unsigned int sip_status_code(const unsigned char *buf, size_t start,
				    size_t limit)
{
	size_t line_end = start;
	size_t code_start;

	while (line_end < limit && buf[line_end] != '\n') {
		++line_end;
	}
	if (line_end == limit || line_end - start < 12 ||
	    memcmp(buf + start, "SIP/", 4) != 0) {
		return 0;
	}
	code_start = start;
	while (code_start < line_end && buf[code_start] != ' ' &&
	       buf[code_start] != '\t') {
		++code_start;
	}
	while (code_start < line_end &&
	       (buf[code_start] == ' ' || buf[code_start] == '\t')) {
		++code_start;
	}
	if (code_start + 3 > line_end || !isdigit(buf[code_start]) ||
	    !isdigit(buf[code_start + 1]) || !isdigit(buf[code_start + 2])) {
		return 0;
	}
	if (code_start + 3 < line_end && buf[code_start + 3] != ' ' &&
	    buf[code_start + 3] != '\t' && buf[code_start + 3] != '\r') {
		return 0;
	}
	return (unsigned int)(buf[code_start] - '0') * 100U +
	       (unsigned int)(buf[code_start + 1] - '0') * 10U +
	       (unsigned int)(buf[code_start + 2] - '0');
}

/* 逐条解析响应消息并输出状态码，初始状态 0 与 AFLNet 约定一致。 */
unsigned int *sip_aflnet_extract_response_codes(unsigned char *buf,
						unsigned int buf_size,
						unsigned int *state_count_ref)
{
	unsigned int *states = (unsigned int *)ck_alloc(sizeof(unsigned int));
	unsigned int state_count = 1;
	size_t cursor = 0;
	size_t total = buf_size;
	states[0] = 0;

	while (cursor < total) {
		size_t line_limit = cursor;
		size_t extent;
		unsigned int status;

		while (line_limit < total && buf[line_limit] != '\n') {
			++line_limit;
		}
		status = sip_status_code(buf, cursor,
			line_limit < total ? line_limit + 1 : line_limit);
		if (status >= 100 && status <= 699) {
			states = (unsigned int *)ck_realloc(states,
				(state_count + 1) * sizeof(unsigned int));
			states[state_count++] = status;
		}
		extent = sip_message_extent(buf, cursor, total);
		if (extent == 0) {
			break;
		}
		cursor += extent;
	}
	*state_count_ref = state_count;
	return states;
}
