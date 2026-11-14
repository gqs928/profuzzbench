#!/usr/bin/env python3
"""Patch AFLNet's SMTP message splitter to keep DATA bodies in one request."""

from pathlib import Path
import difflib
import hashlib
import sys


path = Path(sys.argv[1])
evidence_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/work/build-evidence")
source_dir = path
aflnet_path = source_dir / "aflnet.c"
fuzzer_path = source_dir / "afl-fuzz.c"
text = aflnet_path.read_text(encoding="utf-8")
start = text.index("region_t* extract_requests_smtp(")
end = text.index("\nregion_t* extract_requests_ssh(", start)
old = text[start:end]
if "DATA changes SMTP framing" in old:
    raise SystemExit("AFLNet SMTP DATA-aware patch is already applied")
new = r'''region_t* extract_requests_smtp(unsigned char* buf, unsigned int buf_size, unsigned int* region_count_ref)
{
  unsigned int position = 0;
  unsigned int region_count = 0;
  region_t *regions = NULL;

  while (position < buf_size) {
    unsigned int start = position;
    unsigned int line_end = position;
    unsigned int request_end;
    unsigned int command_length;

    while (line_end + 1 < buf_size &&
           !(buf[line_end] == '\r' && buf[line_end + 1] == '\n')) {
      line_end++;
    }

    if (line_end + 1 >= buf_size) {
      request_end = buf_size;
    } else {
      request_end = line_end + 2;
      command_length = line_end - start;

      /* DATA changes SMTP framing: its body is one request through the
       * line containing only ".", followed by CRLF. */
      if (command_length >= 4 &&
          tolower(buf[start]) == 'd' && tolower(buf[start + 1]) == 'a' &&
          tolower(buf[start + 2]) == 't' && tolower(buf[start + 3]) == 'a' &&
          (command_length == 4 || buf[start + 4] == ' ' || buf[start + 4] == '\t')) {
        unsigned int scan = request_end;
        unsigned int found_terminator = 0;
        while (scan + 2 < buf_size) {
          int line_start = scan == request_end ||
              (scan >= 2 && buf[scan - 2] == '\r' && buf[scan - 1] == '\n');
          if (line_start && buf[scan] == '.' &&
              buf[scan + 1] == '\r' && buf[scan + 2] == '\n') {
            request_end = scan + 3;
            found_terminator = 1;
            break;
          }
          scan++;
        }
        if (!found_terminator) request_end = buf_size;
      }
    }

    region_count++;
    regions = (region_t *)ck_realloc(regions, region_count * sizeof(region_t));
    regions[region_count - 1].start_byte = start;
    regions[region_count - 1].end_byte = request_end - 1;
    regions[region_count - 1].state_sequence = NULL;
    regions[region_count - 1].state_count = 0;
    position = request_end;
  }

  *region_count_ref = region_count;
  return regions;
}'''
if text.count("region_t* extract_requests_smtp(") != 1:
    raise SystemExit("expected exactly one SMTP extractor")
text = text[:start] + new + text[end:]
aflnet_path.write_text(text, encoding="utf-8")
patch_aflnet = "".join(difflib.unified_diff(
    old.splitlines(keepends=True), new.splitlines(keepends=True),
    fromfile="aflnet.c:upstream-extract_requests_smtp",
    tofile="aflnet.c:SMTP-DATA-aware-extractor"))

fuzzer_text = fuzzer_path.read_text(encoding="utf-8")
loop_start = fuzzer_text.index("  for (it = kl_begin(kl_messages); it != kl_end(kl_messages); it = kl_next(it)) {")
loop_end = fuzzer_text.index("\n\nHANDLE_RESPONSES:", loop_start)
old_loop = fuzzer_text[loop_start:loop_end]
if "smtp_data_command_size" in old_loop:
    raise SystemExit("AFLNet SMTP DATA send/response patch is already applied")
new_loop = r'''  for (it = kl_begin(kl_messages); it != kl_end(kl_messages); it = kl_next(it)) {
    char *message = kl_val(it)->mdata;
    unsigned int message_size = kl_val(it)->msize;
    unsigned int smtp_data_command_size = 0;

    if (extract_requests == extract_requests_smtp && message_size >= 6 &&
        tolower((unsigned char)message[0]) == 'd' &&
        tolower((unsigned char)message[1]) == 'a' &&
        tolower((unsigned char)message[2]) == 't' &&
        tolower((unsigned char)message[3]) == 'a') {
      unsigned int i;
      for (i = 0; i + 1 < message_size; i++) {
        if (message[i] == '\r' && message[i + 1] == '\n') {
          unsigned int command_size = i;
          if (command_size == 4 || message[4] == ' ' || message[4] == '\t')
            smtp_data_command_size = i + 2;
          break;
        }
      }
    }

    messages_sent++;
    response_bytes = (u32 *) ck_realloc(response_bytes, messages_sent * sizeof(u32));
    u32 prev_buf_size = response_buf_size;

    if (smtp_data_command_size > 0) {
      n = net_send(sockfd, timeout, message, smtp_data_command_size);
      if (n != smtp_data_command_size) goto HANDLE_RESPONSES;
      if (net_recv(sockfd, timeout, poll_wait_msecs, &response_buf, &response_buf_size))
        goto HANDLE_RESPONSES;

      /* SMTP DATA content must be sent only after the server's 354 reply. */
      u8 got_354 = response_buf_size >= prev_buf_size + 4 &&
          response_buf[prev_buf_size] == '3' &&
          response_buf[prev_buf_size + 1] == '5' &&
          response_buf[prev_buf_size + 2] == '4' &&
          (response_buf[prev_buf_size + 3] == ' ' || response_buf[prev_buf_size + 3] == '-');
      if (got_354 && smtp_data_command_size < message_size) {
        n = net_send(sockfd, timeout, message + smtp_data_command_size,
                     message_size - smtp_data_command_size);
        if (n != message_size - smtp_data_command_size) goto HANDLE_RESPONSES;
        if (net_recv(sockfd, timeout, poll_wait_msecs, &response_buf, &response_buf_size))
          goto HANDLE_RESPONSES;
      }
    } else {
      n = net_send(sockfd, timeout, message, message_size);
      if (n != message_size) goto HANDLE_RESPONSES;
      if (net_recv(sockfd, timeout, poll_wait_msecs, &response_buf, &response_buf_size))
        goto HANDLE_RESPONSES;
    }

    response_bytes[messages_sent - 1] = response_buf_size;
    if (prev_buf_size == response_buf_size) likely_buggy = 1;
    else likely_buggy = 0;
  }'''
fuzzer_text = fuzzer_text[:loop_start] + new_loop + fuzzer_text[loop_end:]
fuzzer_path.write_text(fuzzer_text, encoding="utf-8")
patch_fuzzer = "".join(difflib.unified_diff(
    old_loop.splitlines(keepends=True), new_loop.splitlines(keepends=True),
    fromfile="afl-fuzz.c:upstream-send_over_network-loop",
    tofile="afl-fuzz.c:SMTP-DATA-after-354-loop"))
evidence_dir.mkdir(parents=True, exist_ok=True)
(evidence_dir / "aflnet-smtp-data.patch").write_text(
    patch_aflnet + "\n" + patch_fuzzer, encoding="utf-8")
digests = []
for source in (aflnet_path, fuzzer_path):
    digests.append(f"{hashlib.sha256(source.read_bytes()).hexdigest()}  {source.name}")
(evidence_dir / "aflnet-patched-source.sha256").write_text(
    "\n".join(digests) + "\n", encoding="ascii")
