/* AFLNet 的 IMAP 客户端命令边界与服务端响应状态适配器。 */
#include <ctype.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>

#include "alloc-inl.h"
#include "aflnet.h"

static void imap_add_region(region_t **regions, unsigned int *count,
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

/* 解析 at 位置的 IMAP 字面量标记：有效时返回 1，不是标记时返回 0，
   数据截断或长度溢出时返回 -1。 */
static int imap_literal(const unsigned char *buf, unsigned int size,
                       unsigned int at, unsigned int *after)
{
  unsigned int i = at + 1U;
  uint64_t length = 0;
  unsigned int digits = 0;

  if (at >= size || buf[at] != '{') return 0;
  while (i < size && buf[i] >= '0' && buf[i] <= '9') {
    unsigned int digit = (unsigned int)(buf[i] - '0');
    if (length > (UINT_MAX - digit) / 10U) return -1;
    length = length * 10U + digit;
    digits++;
    i++;
  }
  if (!digits) return 0;
  if (i < size && buf[i] == '+') i++;
  if (i >= size || buf[i] != '}') return 0;
  i++;
  if (size - i < 2U) return -1;
  if (buf[i] != '\r' || buf[i + 1U] != '\n') return 0;
  i += 2U;
  if (length > size - i) return -1;
  *after = i + (unsigned int)length;
  return 1;
}

/* 返回下一条命令的边界。字面量正文按不透明字节处理，因此正文中的
   CRLF 不会把一条 APPEND 命令错误拆成多个区域。 */
static int imap_command_end(const unsigned char *buf, unsigned int size,
                            unsigned int start, unsigned int *end)
{
  unsigned int i = start;
  int quoted = 0, escaped = 0;

  while (i < size) {
    unsigned int after = 0;
    if (!quoted && buf[i] == '{') {
      int literal = imap_literal(buf, size, i, &after);
      if (literal < 0) return 0;
      if (literal > 0) {
        i = after;
        continue;
      }
    }
    if (quoted) {
      if (escaped) escaped = 0;
      else if (buf[i] == '\\') escaped = 1;
      else if (buf[i] == '"') quoted = 0;
    } else if (buf[i] == '"') {
      quoted = 1;
    }
    if (!quoted && buf[i] == '\r' && i + 1U < size && buf[i + 1U] == '\n') {
      *end = i + 1U;
      return 1;
    }
    i++;
  }
  return 0;
}

region_t *extract_requests_imap(unsigned char *buf, unsigned int buf_size,
                                unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0, start = 0;

  if (!region_count_ref) return NULL;
  if (!buf || !buf_size) {
    *region_count_ref = 0;
    return NULL;
  }
  if (buf_size > (unsigned int)INT_MAX) {
    imap_add_region(&regions, &count, 0U, (unsigned int)INT_MAX - 1U);
    *region_count_ref = count;
    return regions;
  }
  while (start < buf_size) {
    unsigned int end = 0;
    if (!imap_command_end(buf, buf_size, start, &end) || end < start) {
      imap_add_region(&regions, &count, start, buf_size - 1U);
      break;
    }
    imap_add_region(&regions, &count, start, end);
    start = end + 1U;
  }
  *region_count_ref = count;
  return regions;
}

static int imap_token_equal(const unsigned char *buf, unsigned int length,
                            const char *word)
{
  unsigned int i;
  if (strlen(word) != length) return 0;
  for (i = 0; i < length; i++)
    if ((unsigned char)toupper(buf[i]) != (unsigned char)word[i]) return 0;
  return 1;
}

static unsigned int imap_token_state(const unsigned char *buf,
                                     unsigned int length)
{
  uint32_t hash = 2166136261U;
  unsigned int i;
  for (i = 0; i < length; i++) {
    hash ^= (unsigned char)toupper(buf[i]);
    hash *= 16777619U;
  }
  return 100U + (hash % 60000U);
}

static unsigned int imap_status_state(const unsigned char *buf,
                                     unsigned int length, int tagged)
{
  unsigned int base = tagged ? 10U : 1U;
  if (imap_token_equal(buf, length, "OK")) return base;
  if (imap_token_equal(buf, length, "NO")) return base + 1U;
  if (imap_token_equal(buf, length, "BAD")) return base + 2U;
  if (imap_token_equal(buf, length, "BYE")) return base + 3U;
  return imap_token_state(buf, length);
}

/* 按响应开头的原子字段分类，忽略动态标签、数量、邮箱名和说明文本，
   让同一协议状态在重复回放时得到稳定编号。 */
static unsigned int imap_response_state(const unsigned char *line,
                                       unsigned int length)
{
  unsigned int i = 0, first_start, first_length, second_start, second_length;
  while (i < length && (line[i] == ' ' || line[i] == '\t')) i++;
  if (i == length) return 0U;
  if (line[i] == '+') return 20U;
  if (line[i] == '*') {
    i++;
    while (i < length && (line[i] == ' ' || line[i] == '\t')) i++;
    first_start = i;
    while (i < length && line[i] != ' ' && line[i] != '\t') i++;
    first_length = i - first_start;
    if (first_length == 0) return 30U;
    if (imap_token_equal(line + first_start, first_length, "OK") ||
        imap_token_equal(line + first_start, first_length, "NO") ||
        imap_token_equal(line + first_start, first_length, "BAD") ||
        imap_token_equal(line + first_start, first_length, "BYE"))
      return imap_status_state(line + first_start, first_length, 0);
    /* 无标签数字响应的第二个字段才是实际语义原子。 */
    if (first_length && isdigit(line[first_start])) {
      while (i < length && (line[i] == ' ' || line[i] == '\t')) i++;
      first_start = i;
      while (i < length && line[i] != ' ' && line[i] != '\t') i++;
      first_length = i - first_start;
    }
    return imap_token_state(line + first_start, first_length);
  }

  /* 带标签响应忽略客户端选择的标签，只分类服务端状态字段。 */
  while (i < length && line[i] != ' ' && line[i] != '\t') i++;
  while (i < length && (line[i] == ' ' || line[i] == '\t')) i++;
  second_start = i;
  while (i < length && line[i] != ' ' && line[i] != '\t') i++;
  second_length = i - second_start;
  if (!second_length) return 30U;
  return imap_status_state(line + second_start, second_length, 1);
}

static void imap_add_state(unsigned int **states, unsigned int *count,
                           unsigned int state)
{
  *states = (unsigned int *)ck_realloc(*states, (*count + 1U) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

unsigned int *extract_response_codes_imap(unsigned char *buf,
                                          unsigned int buf_size,
                                          unsigned int *state_count_ref)
{
  unsigned int *states = NULL;
  unsigned int count = 0, pos = 0;

  if (!state_count_ref) return NULL;
  imap_add_state(&states, &count, 0U);
  if (!buf || !buf_size) {
    *state_count_ref = count;
    return states;
  }

  while (pos < buf_size) {
    unsigned int line_start = pos, line_end = 0;
    int quoted = 0, escaped = 0, complete = 0;
    while (pos < buf_size) {
      unsigned int after = 0;
      if (!quoted && buf[pos] == '{') {
        int literal = imap_literal(buf, buf_size, pos, &after);
        if (literal < 0) { pos = buf_size; break; }
        if (literal > 0) { pos = after; continue; }
      }
      if (quoted) {
        if (escaped) escaped = 0;
        else if (buf[pos] == '\\') escaped = 1;
        else if (buf[pos] == '"') quoted = 0;
      } else if (buf[pos] == '"') {
        quoted = 1;
      }
      if (!quoted && buf[pos] == '\r' && pos + 1U < buf_size &&
          buf[pos + 1U] == '\n') {
        line_end = pos;
        pos += 2U;
        complete = 1;
        break;
      }
      pos++;
    }
    if (!complete) break;
    imap_add_state(&states, &count,
                   imap_response_state(buf + line_start, line_end - line_start));
  }

  *state_count_ref = count;
  return states;
}
