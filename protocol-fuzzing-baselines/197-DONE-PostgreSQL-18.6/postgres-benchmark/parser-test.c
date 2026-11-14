#include <stdio.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static void put_u32(unsigned char *buf, unsigned int value)
{
  buf[0] = (unsigned char)(value >> 24);
  buf[1] = (unsigned char)(value >> 16);
  buf[2] = (unsigned char)(value >> 8);
  buf[3] = (unsigned char)value;
}

static unsigned int append_backend(unsigned char *buf, unsigned int offset,
                                   unsigned char type,
                                   const unsigned char *body,
                                   unsigned int body_size)
{
  buf[offset] = type;
  put_u32(buf + offset + 1U, body_size + 4U);
  if (body_size) memcpy(buf + offset + 5U, body, body_size);
  return offset + body_size + 5U;
}

static int check_regions(unsigned char *buf, unsigned int size,
                         const int *starts, const int *ends,
                         unsigned int expected_count)
{
  unsigned int count = 0, i;
  region_t *regions = extract_requests_postgres(buf, size, &count);
  int ok = count == expected_count;

  if (ok) {
    for (i = 0; i < count; i++) {
      if (regions[i].start_byte != starts[i] || regions[i].end_byte != ends[i]) {
        fprintf(stderr, "报文区间 %u 错误：得到 %d..%d，预期 %d..%d\n", i,
                regions[i].start_byte, regions[i].end_byte,
                starts[i], ends[i]);
        ok = 0;
        break;
      }
    }
  }
  ck_free(regions);
  return ok;
}

static int check_states(unsigned char *buf, unsigned int size,
                        const unsigned int *expected,
                        unsigned int expected_count)
{
  unsigned int count = 0, i;
  unsigned int *states =
      extract_response_codes_postgres(buf, size, &count);
  int ok = count == expected_count;

  if (ok) {
    for (i = 0; i < count; i++) {
      if (states[i] != expected[i]) {
        fprintf(stderr, "响应状态 %u 错误：得到 %u，预期 %u\n", i,
                states[i], expected[i]);
        ok = 0;
        break;
      }
    }
  } else {
    fprintf(stderr, "响应状态数量错误：得到 %u，预期 %u\n",
            count, expected_count);
  }
  ck_free(states);
  return ok;
}

int main(void)
{
  unsigned char requests[] = {
      0, 0, 0, 8, 0, 3, 0, 0,
      'Q', 0, 0, 0, 14, 'S', 'E', 'L', 'E', 'C', 'T', ' ', '1', ';', 0,
      'X', 0, 0, 0, 4};
  unsigned char ssl_then_startup[] = {
      0, 0, 0, 8, 4, 210, 22, 47,
      0, 0, 0, 8, 0, 3, 0, 0,
      'Q', 0, 0, 0, 14, 'S', 'E', 'L', 'E', 'C', 'T', ' ', '1', ';', 0};
  unsigned char malformed_tail[] = {
      0, 0, 0, 8, 0, 3, 0, 0, 'Q', 255, 255, 255, 255};
  unsigned char responses[512];
  const int three_starts[] = {0, 8, 23};
  const int three_ends[] = {7, 22, 27};
  const int ssl_starts[] = {0, 8, 16};
  const int ssl_ends[] = {7, 15, 30};
  const int malformed_starts[] = {0, 8};
  const int malformed_ends[] = {7, 12};
  const unsigned char auth_ok[] = {0, 0, 0, 0};
  const unsigned char auth_cleartext[] = {0, 0, 0, 3};
  const unsigned char ready_idle[] = {'I'};
  const unsigned char ready_tx[] = {'T'};
  const unsigned char ready_failed[] = {'E'};
  const unsigned char parse_complete[] = {0};
  const unsigned char copy_response[] = {0};
  const unsigned char protocol_negotiate[] = {0, 3, 0, 0};
  const unsigned char error_body[] = {
      'S', 'E', 'R', 'R', 'O', 'R', 0,
      'C', '4', '2', '6', '0', '1', 0,
      'M', 's', 'y', 'n', 't', 'a', 'x', ' ', 'e', 'r', 'r', 'o', 'r', 0,
      0};
  const unsigned char auth_error_body[] = {
      'S', 'F', 'A', 'T', 'A', 'L', 0,
      'C', '2', '8', 'P', '0', '1', 0,
      'M', 'p', 'a', 's', 's', 'w', 'o', 'r', 'd', ' ', 'f', 'a', 'i', 'l',
      'e', 'd', 0, 0};
  const unsigned int expected[] = {
      0, 54, 1, 2, 51, 52, 21, 22, 23, 20, 41,
      11, 12, 10, 30, 53, 40};
  unsigned int response_size = 0;

  if (!check_regions(requests, sizeof(requests), three_starts, three_ends, 3)) {
    fprintf(stderr, "Startup、Query、Terminate 报文边界测试失败\n");
    return 1;
  }
  if (!check_regions(ssl_then_startup, sizeof(ssl_then_startup),
                     ssl_starts, ssl_ends, 3)) {
    fprintf(stderr, "SSLRequest 后 StartupMessage 边界测试失败\n");
    return 1;
  }
  if (!check_regions(malformed_tail, sizeof(malformed_tail),
                     malformed_starts, malformed_ends, 2)) {
    fprintf(stderr, "畸形长度尾部保留测试失败\n");
    return 1;
  }

  responses[response_size++] = 'N';
  response_size = append_backend(responses, response_size, 'R',
                                 auth_ok, sizeof(auth_ok));
  response_size = append_backend(responses, response_size, 'R',
                                 auth_cleartext, sizeof(auth_cleartext));
  response_size = append_backend(responses, response_size, 'S',
                                 (const unsigned char *)"server_version\0" "18.6\0",
                                 20U);
  response_size = append_backend(responses, response_size, 'K',
                                 (const unsigned char *)"12345678", 8U);
  response_size = append_backend(responses, response_size, 'T',
                                 NULL, 0U);
  response_size = append_backend(responses, response_size, 'D',
                                 NULL, 0U);
  response_size = append_backend(responses, response_size, '1',
                                 parse_complete, sizeof(parse_complete));
  response_size = append_backend(responses, response_size, 'C',
                                 (const unsigned char *)"SELECT 1", 9U);
  response_size = append_backend(responses, response_size, 'E',
                                 error_body, sizeof(error_body));
  response_size = append_backend(responses, response_size, 'Z',
                                 ready_tx, sizeof(ready_tx));
  response_size = append_backend(responses, response_size, 'Z',
                                 ready_failed, sizeof(ready_failed));
  response_size = append_backend(responses, response_size, 'Z',
                                 ready_idle, sizeof(ready_idle));
  response_size = append_backend(responses, response_size, 'G',
                                 copy_response, sizeof(copy_response));
  response_size = append_backend(responses, response_size, 'v',
                                 protocol_negotiate,
                                 sizeof(protocol_negotiate));
  response_size = append_backend(responses, response_size, 'E',
                                 auth_error_body,
                                 sizeof(auth_error_body));

  if (!check_states(responses, response_size, expected,
                    sizeof(expected) / sizeof(expected[0]))) {
    fprintf(stderr, "响应消息状态映射测试失败\n");
    return 1;
  }
  puts("通过：Startup/SSL/常规报文切分、畸形尾部保留与 PostgreSQL 状态映射。");
  return 0;
}
