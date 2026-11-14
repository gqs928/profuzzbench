#define _GNU_SOURCE

#include <dlfcn.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

/* Test-only fault injection. It changes no InspIRCd source or protocol code. */
/* One-bit mutation in a valid IRC request: "PING X\r\n" -> "PING Y\r\n". */
static const char trigger[] = "PING Y\r\n";
static ssize_t (*real_recv)(int, void *, size_t, int);

ssize_t recv(int fd, void *buffer, size_t length, int flags)
{
  if (!real_recv)
    real_recv = (ssize_t (*)(int, void *, size_t, int))dlsym(RTLD_NEXT, "recv");
  if (!real_recv)
    _exit(125);

  ssize_t received = real_recv(fd, buffer, length, flags);
  if (received > 0 && memmem(buffer, (size_t)received, trigger, sizeof(trigger) - 1))
  {
    static const char notice[] = "CONTROLLED_IRC_CRASH_TRIGGERED\n";
    (void)write(STDERR_FILENO, notice, sizeof(notice) - 1);
    abort();
  }
  return received;
}
