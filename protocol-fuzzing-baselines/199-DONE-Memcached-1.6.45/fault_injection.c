/* Acceptance-only LD_PRELOAD hook; never loaded by the normal image runner.
 * A dedicated request causes a deterministic process abort to test whether
 * AFLNet records a server crash and whether the resulting sample replays. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/socket.h>

static void maybe_abort(const void *buffer, ssize_t size)
{
  static const char trigger[] = "CRASHNOW";
  if (size >= (ssize_t)(sizeof(trigger) - 1) &&
      !memcmp(buffer, trigger, sizeof(trigger) - 1)) abort();
}

ssize_t recv(int fd, void *buffer, size_t size, int flags)
{
  static ssize_t (*real_recv)(int, void *, size_t, int);
  ssize_t result;
  if (!real_recv) real_recv = dlsym(RTLD_NEXT, "recv");
  if (!real_recv) abort();
  result = real_recv(fd, buffer, size, flags);
  if (result > 0) maybe_abort(buffer, result);
  return result;
}

ssize_t read(int fd, void *buffer, size_t size)
{
  static ssize_t (*real_read)(int, void *, size_t);
  ssize_t result;
  if (!real_read) real_read = dlsym(RTLD_NEXT, "read");
  if (!real_read) abort();
  result = real_read(fd, buffer, size);
  if (result > 0) maybe_abort(buffer, result);
  return result;
}
