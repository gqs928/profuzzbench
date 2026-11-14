#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;

static void on_signal(int signal_number) {
  (void)signal_number;
  stop_requested = 1;
}

static void sleep_millis(long milliseconds) {
  struct timespec delay = {milliseconds / 1000,
                           (milliseconds % 1000) * 1000000L};
  while (nanosleep(&delay, &delay) < 0 && errno == EINTR) {
  }
}

static int tgtadm(const char *prefix, char *const arguments[]) {
  char executable[1024];
  if (snprintf(executable, sizeof(executable), "%s/sbin/tgtadm", prefix) >=
      (int)sizeof(executable)) {
    return -1;
  }

  pid_t child = fork();
  if (child < 0) {
    return -1;
  }
  if (child == 0) {
    int null_fd = open("/dev/null", O_WRONLY);
    if (null_fd >= 0) {
      (void)dup2(null_fd, STDOUT_FILENO);
      (void)close(null_fd);
    }
    execv(executable, arguments);
    _exit(127);
  }

  int status = 0;
  while (waitpid(child, &status, 0) < 0) {
    if (errno != EINTR) {
      return -1;
    }
  }
  return WIFEXITED(status) && WEXITSTATUS(status) == 0 ? 0 : -1;
}

static void stop_daemon(pid_t daemon_pid) {
  if (daemon_pid <= 0) {
    return;
  }
  (void)kill(daemon_pid, SIGTERM);
  for (int attempt = 0; attempt < 20; ++attempt) {
    int status;
    pid_t result = waitpid(daemon_pid, &status, WNOHANG);
    if (result == daemon_pid || (result < 0 && errno == ECHILD)) {
      return;
    }
    sleep_millis(50);
  }
  (void)kill(daemon_pid, SIGKILL);
  while (waitpid(daemon_pid, NULL, 0) < 0 && errno == EINTR) {
  }
}

static int run_target(const char *prefix) {
  const char *ipc = getenv("TGT_IPC_SOCKET");
  if (ipc == NULL || *ipc == '\0') {
    ipc = "/tmp/tgt-benchmark-ipc";
    (void)setenv("TGT_IPC_SOCKET", ipc, 1);
  }
  const char *backing = getenv("BACKING_STORE");
  if (backing == NULL || *backing == '\0') {
    backing = "/tmp/tgt-benchmark.img";
  }

  char ipc_suffix[1100];
  char pidfile[1100];
  if (snprintf(ipc_suffix, sizeof(ipc_suffix), "%s.0", ipc) >=
          (int)sizeof(ipc_suffix) ||
      snprintf(pidfile, sizeof(pidfile), "%s.pid", ipc) >=
          (int)sizeof(pidfile)) {
    fprintf(stderr, "tgt-runner: IPC path too long\n");
    return 2;
  }
  (void)unlink(ipc);
  (void)unlink(ipc_suffix);
  (void)unlink(pidfile);

  int backing_fd = open(backing, O_CREAT | O_RDWR, 0600);
  if (backing_fd < 0 || ftruncate(backing_fd, 16 * 1024 * 1024) < 0) {
    fprintf(stderr, "tgt-runner: cannot initialize backing store %s: %s\n",
            backing, strerror(errno));
    if (backing_fd >= 0) {
      close(backing_fd);
    }
    return 2;
  }
  close(backing_fd);

  char tgtd_path[1024];
  if (snprintf(tgtd_path, sizeof(tgtd_path), "%s/sbin/tgtd", prefix) >=
      (int)sizeof(tgtd_path)) {
    fprintf(stderr, "tgt-runner: tgt prefix too long\n");
    return 2;
  }
  pid_t daemon_pid = fork();
  if (daemon_pid < 0) {
    perror("tgt-runner: fork tgtd");
    return 2;
  }
  if (daemon_pid == 0) {
    /* Keep the runner's forkserver in control; tgt still writes coverage to
       the inherited shared map, but must not start a nested forkserver. */
    (void)close(198);
    (void)close(199);
    execl(tgtd_path, "tgtd", "-f", (char *)NULL);
    perror("tgt-runner: exec tgtd");
    _exit(127);
  }

  char *show_args[] = {"tgtadm", "--lld", "iscsi", "--op", "show", "--mode",
                       "target", NULL};
  bool ready = false;
  for (int attempt = 0; attempt < 100; ++attempt) {
    int status;
    pid_t result = waitpid(daemon_pid, &status, WNOHANG);
    if (result == daemon_pid) {
      fprintf(stderr, "tgt-runner: tgtd exited during startup\n");
      return 2;
    }
    if (tgtadm(prefix, show_args) == 0) {
      ready = true;
      break;
    }
    sleep_millis(50);
  }
  if (!ready) {
    fprintf(stderr, "tgt-runner: tgtd management socket did not become ready\n");
    stop_daemon(daemon_pid);
    return 2;
  }

  char *new_target_args[] = {"tgtadm", "--lld", "iscsi", "--op", "new", "--mode",
                             "target", "--tid", "1", "--targetname",
                             "iqn.2026-11.invalid:codex-tgt", NULL};
  char *new_lun_args[] = {"tgtadm", "--lld", "iscsi", "--op", "new", "--mode",
                          "logicalunit", "--tid", "1", "--lun", "1",
                          "--backing-store", (char *)backing, NULL};
  char *bind_args[] = {"tgtadm", "--lld", "iscsi", "--op", "bind", "--mode",
                       "target", "--tid", "1", "--initiator-address", "ALL", NULL};
  if (tgtadm(prefix, new_target_args) != 0 || tgtadm(prefix, new_lun_args) != 0 ||
      tgtadm(prefix, bind_args) != 0) {
    fprintf(stderr, "tgt-runner: failed to configure the iSCSI target\n");
    stop_daemon(daemon_pid);
    return 2;
  }

  struct sigaction action;
  memset(&action, 0, sizeof(action));
  action.sa_handler = on_signal;
  sigemptyset(&action.sa_mask);
  (void)sigaction(SIGTERM, &action, NULL);
  (void)sigaction(SIGINT, &action, NULL);
  while (!stop_requested) {
    sleep_millis(100);
    int status;
    pid_t result = waitpid(daemon_pid, &status, WNOHANG);
    if (result == daemon_pid) {
      fprintf(stderr, "tgt-runner: tgtd exited unexpectedly\n");
      return 1;
    }
  }
  stop_daemon(daemon_pid);
  (void)unlink(ipc);
  (void)unlink(ipc_suffix);
  (void)unlink(pidfile);
  (void)unlink(backing);
  return 0;
}

int main(void) {
  const char *prefix = getenv("TGT_PREFIX");
  if (prefix == NULL || *prefix == '\0') {
    prefix = "/opt/tgt-afl";
  }
  return run_target(prefix);
}
