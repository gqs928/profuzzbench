#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

region_t *extract_requests_imap(unsigned char *, unsigned int, unsigned int *);
unsigned int *extract_response_codes_imap(unsigned char *, unsigned int,
                                         unsigned int *);

static void require(int condition, const char *message)
{
  if (!condition) {
    fprintf(stderr, "失败：%s\n", message);
    exit(1);
  }
}

int main(void)
{
  unsigned char commands[] =
      "A1 NOOP\r\nB1 LOGIN fuzzuser \"带空格\"\r\n";
  unsigned char literal[] =
      "A2 APPEND INBOX {6+}\r\na\r\nb\r\n\r\nA3 LOGOUT\r\n";
  unsigned char truncated[] = "A4 APPEND INBOX {9+}\r\nabc";
  unsigned char responses[] =
      "* OK ready\r\n* 2 EXISTS\r\nA1 OK complete\r\n+ continue\r\n";
  region_t *regions;
  unsigned int *states;
  unsigned int count = 0;
  unsigned int states_count = 0;

  regions = extract_requests_imap(commands, sizeof(commands) - 1U, &count);
  require(count == 2U, "普通命令按 CRLF 拆成两个请求");
  require(regions[0].start_byte == 0 && regions[0].end_byte == 8,
          "第一条命令保留结尾 CRLF");
  require(regions[1].start_byte == 9 &&
          regions[1].end_byte == sizeof(commands) - 2U,
          "带引号参数的命令保持完整");
  ck_free(regions);

  regions = extract_requests_imap(literal, sizeof(literal) - 1U, &count);
  require(count == 2U, "字面量正文内的 CRLF 不拆开 APPEND");
  require(regions[0].end_byte ==
              (int)(strstr((char *)literal, "A3 LOGOUT") - (char *)literal) - 1,
          "APPEND 区域包含完整字面量正文及命令终止符");
  ck_free(regions);

  regions = extract_requests_imap(truncated, sizeof(truncated) - 1U, &count);
  require(count == 1U && regions[0].start_byte == 0,
          "截断字面量保留为一个尾部请求");
  ck_free(regions);

  states = extract_response_codes_imap(responses, sizeof(responses) - 1U,
                                       &states_count);
  require(states_count == 5U, "状态解析包含哨兵和四条服务端响应");
  require(states[0] == 0U && states[1] == 1U && states[2] >= 100U &&
          states[3] == 10U && states[4] == 20U,
          "欢迎、未标记、带标记及继续响应拥有不同状态编号");
  ck_free(states);

  puts("通过：IMAP 命令边界、字面量、截断输入和响应状态解析");
  return 0;
}
