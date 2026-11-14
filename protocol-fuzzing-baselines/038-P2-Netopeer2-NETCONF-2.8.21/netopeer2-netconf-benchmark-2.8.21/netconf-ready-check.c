#include <arpa/inet.h>
#include <netinet/in.h>
#include <signal.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;

static void handle_sigterm(int signal_number) {
  (void)signal_number;
  stop_requested = 1;
}

static int ssh_server_responds(void) {
  for (int attempt = 0; attempt < 3; attempt++) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return 0;

    struct timeval timeout = {.tv_sec = 0, .tv_usec = 200000};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(830);
    if (inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr) != 1) {
      close(fd);
      return 0;
    }

    int rc = connect(fd, (struct sockaddr *)&addr, sizeof(addr));
    char banner[128];
    ssize_t size = rc == 0 ? recv(fd, banner, sizeof(banner), 0) : -1;
    close(fd);
    if (size >= 8 && memcmp(banner, "SSH-2.0-", 8) == 0 &&
        memchr(banner, '\n', (size_t)size) != NULL) return 1;
    usleep(100000);
  }
  return 0;
}

static void report_service_failure(void) {
  /* AFLNet records this signal as the testcase that left the service down. */
  signal(SIGSEGV, SIG_DFL);
  raise(SIGSEGV);
  _exit(128 + SIGSEGV);
}

int main(int argc, char **argv) {
  if (argc == 2 && strcmp(argv[1], "--once") == 0)
    return ssh_server_responds() ? 0 : 1;

  struct sigaction action = {0};
  action.sa_handler = handle_sigterm;
  sigemptyset(&action.sa_mask);
  if (sigaction(SIGTERM, &action, NULL) != 0) return 2;

  /* Check before AFLNet sends a testcase, then remain alive until -K. */
  if (!ssh_server_responds()) return 1;
  while (!stop_requested) pause();

  /* Check again after the testcase so an external server crash is visible. */
  if (!ssh_server_responds()) report_service_failure();
  return 0;
}
