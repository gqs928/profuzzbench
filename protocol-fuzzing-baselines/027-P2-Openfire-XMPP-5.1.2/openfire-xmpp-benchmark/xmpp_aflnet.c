/* XMPP-over-TCP request and response-state adapter for AFLNet.
 * Each client XML top-level stanza is a request region. The long-lived
 * stream:stream opener is a separate region so AFLNet can mutate the stream
 * setup and subsequent stanzas independently. */
#include <ctype.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

typedef struct {
  unsigned int name_start;
  unsigned int name_end;
  unsigned int tag_end;
  unsigned char closing;
  unsigned char self_closing;
} xmpp_tag_t;

static int xmpp_starts_with(const unsigned char *buf, unsigned int size,
                            unsigned int at, const char *text)
{
  unsigned int length = (unsigned int)strlen(text);
  return at <= size && length <= size - at &&
         memcmp(buf + at, text, length) == 0;
}

static unsigned int xmpp_find(const unsigned char *buf, unsigned int size,
                              unsigned int at, const char *text)
{
  unsigned int i, length = (unsigned int)strlen(text);
  if (length > size || at > size - length) return size;
  for (i = at; i <= size - length; i++)
    if (memcmp(buf + i, text, length) == 0) return i;
  return size;
}

static int xmpp_parse_tag(const unsigned char *buf, unsigned int size,
                          unsigned int start, xmpp_tag_t *tag)
{
  unsigned int i, name_start;
  unsigned char quote = 0;
  if (start >= size || buf[start] != '<') return 0;
  i = start + 1;
  if (i < size && buf[i] == '/') {
    tag->closing = 1;
    i++;
  } else {
    tag->closing = 0;
  }
  while (i < size && isspace((unsigned char)buf[i])) i++;
  name_start = i;
  while (i < size && !isspace((unsigned char)buf[i]) &&
         buf[i] != '/' && buf[i] != '>' && buf[i] != '?') i++;
  if (i == name_start) return 0;
  tag->name_start = name_start;
  tag->name_end = i;
  tag->tag_end = size;
  tag->self_closing = 0;
  for (; i < size; i++) {
    unsigned char c = buf[i];
    if (quote) {
      if (c == quote) quote = 0;
    } else if (c == '\'' || c == '"') {
      quote = c;
    } else if (c == '>') {
      unsigned int before = i;
      while (before > name_start && isspace((unsigned char)buf[before - 1]))
        before--;
      tag->self_closing = !tag->closing && before > name_start &&
                          buf[before - 1] == '/';
      tag->tag_end = i;
      return 1;
    }
  }
  return 1;
}

static int xmpp_tag_is_stream_open(const unsigned char *buf,
                                   const xmpp_tag_t *tag)
{
  return !tag->closing &&
         tag->name_end - tag->name_start == 13 &&
         memcmp(buf + tag->name_start, "stream:stream", 13) == 0;
}

static int xmpp_tag_is_stream_close(const unsigned char *buf,
                                    const xmpp_tag_t *tag)
{
  return tag->closing &&
         tag->name_end - tag->name_start == 13 &&
         memcmp(buf + tag->name_start, "stream:stream", 13) == 0;
}

static void xmpp_append_region(region_t **regions, unsigned int *count,
                               unsigned int start, unsigned int end)
{
  if (end < start) return;
  *regions = (region_t *)ck_realloc(*regions,
                                    (*count + 1) * sizeof(region_t));
  (*regions)[*count].start_byte = (int)start;
  (*regions)[*count].end_byte = (int)end;
  (*regions)[*count].modifiable = 1;
  (*regions)[*count].state_sequence = NULL;
  (*regions)[*count].state_count = 0;
  (*count)++;
}

region_t *extract_requests_xmpp(unsigned char *buf, unsigned int buf_size,
                                unsigned int *region_count_ref)
{
  region_t *regions = NULL;
  unsigned int count = 0, start = 0, i = 0, depth = 0;
  if (!buf || !buf_size) {
    *region_count_ref = 0;
    return NULL;
  }
  while (i < buf_size) {
    xmpp_tag_t tag;
    unsigned int end;
    if (buf[i] != '<') { i++; continue; }
    if (xmpp_starts_with(buf, buf_size, i, "<!--")) {
      end = xmpp_find(buf, buf_size, i + 4, "-->");
      i = end == buf_size ? buf_size : end + 3;
      continue;
    }
    if (xmpp_starts_with(buf, buf_size, i, "<![CDATA[")) {
      end = xmpp_find(buf, buf_size, i + 9, "]]>");
      i = end == buf_size ? buf_size : end + 3;
      continue;
    }
    if (xmpp_starts_with(buf, buf_size, i, "<?")) {
      end = xmpp_find(buf, buf_size, i + 2, "?>");
      i = end == buf_size ? buf_size : end + 2;
      continue;
    }
    if (i + 1 < buf_size && buf[i + 1] == '!') {
      end = xmpp_find(buf, buf_size, i + 2, ">");
      i = end == buf_size ? buf_size : end + 1;
      continue;
    }
    if (!xmpp_parse_tag(buf, buf_size, i, &tag)) { i++; continue; }
    end = tag.tag_end;
    if (xmpp_tag_is_stream_open(buf, &tag) && depth == 0) {
      xmpp_append_region(&regions, &count, start, end);
      start = end + 1;
    } else if (tag.closing) {
      if (depth > 0) depth--;
      if (depth == 0) {
        xmpp_append_region(&regions, &count, start, end);
        start = end + 1;
      }
    } else if (tag.self_closing) {
      if (depth == 0) {
        xmpp_append_region(&regions, &count, start, end);
        start = end + 1;
      }
    } else {
      depth++;
    }
    i = end < buf_size ? end + 1 : buf_size;
  }
  if (start < buf_size) xmpp_append_region(&regions, &count, start, buf_size - 1);
  *region_count_ref = count;
  return regions;
}

static int xmpp_name_equals(const unsigned char *buf, unsigned int start,
                            unsigned int end, const char *name)
{
  unsigned int i, length = (unsigned int)strlen(name);
  if (end - start != length) return 0;
  for (i = 0; i < length; i++)
    if (tolower((unsigned char)buf[start + i]) !=
        tolower((unsigned char)name[i])) return 0;
  return 1;
}

static unsigned int xmpp_tag_state(const unsigned char *buf,
                                   const xmpp_tag_t *tag)
{
  unsigned int start = tag->name_start, end = tag->name_end, i, hash = 2166136261u;
  static const struct { const char *name; unsigned int state; } fixed[] = {
    {"stream:stream", 1001}, {"stream:features", 1002},
    {"features", 1002}, {"starttls", 1003}, {"proceed", 1004},
    {"mechanisms", 1005}, {"mechanism", 1006}, {"auth", 1007},
    {"challenge", 1008}, {"response", 1009}, {"success", 1010},
    {"failure", 1011}, {"presence", 1015}, {"message", 1016},
    {"error", 1017}, {"stream:error", 1018}
  };
  unsigned int local = start;
  if (tag->closing && xmpp_name_equals(buf, start, end, "stream:stream"))
    return 1019;
  for (i = start; i < end; i++) if (buf[i] == ':') local = i + 1;
  if (xmpp_name_equals(buf, start, end, "iq")) {
    unsigned int p = end, limit = tag->tag_end;
    while (p < limit) {
      if (xmpp_starts_with(buf, limit, p, "type")) {
        unsigned int q = p + 4;
        while (q < limit && isspace((unsigned char)buf[q])) q++;
        if (q < limit && buf[q++] == '=') {
          while (q < limit && isspace((unsigned char)buf[q])) q++;
          if (q < limit && (buf[q] == '\'' || buf[q] == '"')) {
            unsigned char quote = buf[q++];
            if (xmpp_starts_with(buf, limit, q, "result")) return 1012;
            if (xmpp_starts_with(buf, limit, q, "error")) return 1013;
            if (quote == buf[q]) return 1014;
            return 1014;
          }
        }
      }
      p++;
    }
    return 1014;
  }
  for (i = 0; i < sizeof(fixed) / sizeof(fixed[0]); i++)
    if (xmpp_name_equals(buf, start, end, fixed[i].name)) return fixed[i].state;
  /* Namespaced extension tags use their local name for stable state IDs. */
  for (i = local; i < end; i++)
    hash = (hash ^ (unsigned int)tolower((unsigned char)buf[i])) * 16777619u;
  return 2000u + hash % 1000000u;
}

static void xmpp_append_state(unsigned int **states, unsigned int *count,
                              unsigned int state)
{
  *states = (unsigned int *)ck_realloc(*states,
                                       (*count + 1) * sizeof(unsigned int));
  (*states)[(*count)++] = state;
}

unsigned int *extract_response_codes_xmpp(unsigned char *buf,
                                          unsigned int buf_size,
                                          unsigned int *state_count_ref)
{
  unsigned int *states = NULL, count = 0, i = 0;
  xmpp_append_state(&states, &count, 0);
  if (buf) {
    while (i < buf_size) {
      xmpp_tag_t tag;
      unsigned int end;
      if (buf[i] != '<') { i++; continue; }
      if (xmpp_starts_with(buf, buf_size, i, "<!--")) {
        end = xmpp_find(buf, buf_size, i + 4, "-->");
        i = end == buf_size ? buf_size : end + 3;
        continue;
      }
      if (xmpp_starts_with(buf, buf_size, i, "<![CDATA[")) {
        end = xmpp_find(buf, buf_size, i + 9, "]]>");
        i = end == buf_size ? buf_size : end + 3;
        continue;
      }
      if (xmpp_starts_with(buf, buf_size, i, "<?")) {
        end = xmpp_find(buf, buf_size, i + 2, "?>");
        i = end == buf_size ? buf_size : end + 2;
        continue;
      }
      if (!xmpp_parse_tag(buf, buf_size, i, &tag)) { i++; continue; }
      if (!tag.closing || xmpp_tag_is_stream_close(buf, &tag))
        xmpp_append_state(&states, &count, xmpp_tag_state(buf, &tag));
      end = tag.tag_end;
      i = end < buf_size ? end + 1 : buf_size;
    }
  }
  *state_count_ref = count;
  return states;
}
