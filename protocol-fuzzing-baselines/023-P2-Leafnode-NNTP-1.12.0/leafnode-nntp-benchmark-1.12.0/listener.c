#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

extern int leafnode_nntpd_main(int argc, char **argv);

static int reset_fixture(const char *prefix)
{
  pid_t pid = fork();
  int status;
  if (pid < 0) return -1;
  if (pid == 0) {
    execl("/usr/bin/python3", "python3", "/opt/benchmark/reset_spool.py",
          prefix, (char *)NULL);
    _exit(127);
  }
  while (waitpid(pid, &status, 0) < 0) {
    if (errno != EINTR) return -1;
  }
  return WIFEXITED(status) && WEXITSTATUS(status) == 0 ? 0 : -1;
}

int main(int argc, char **argv)
{
  struct sockaddr_in address;
  const char *prefix = getenv("LEAFNODE_PREFIX");
  int server;
  if (!prefix) prefix = "/opt/leafnode-afl";
  server = socket(AF_INET, SOCK_STREAM, 0);
  if (server < 0) { perror("socket"); return 1; }
  {
    int yes = 1;
    (void)setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
  }
  memset(&address, 0, sizeof(address));
  address.sin_family = AF_INET;
  address.sin_port = htons(1119);
  address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  if (bind(server, (struct sockaddr *)&address, sizeof(address)) < 0 ||
      listen(server, 32) < 0) {
    perror("bind/listen");
    close(server);
    return 1;
  }
  for (;;) {
    int client;
    pid_t child;
    while (waitpid(-1, NULL, WNOHANG) > 0) { }
    client = accept(server, NULL, NULL);
    if (client < 0) {
      if (errno == EINTR) continue;
      perror("accept");
      return 1;
    }
    if (reset_fixture(prefix) < 0) {
      perror("reset Leafnode spool fixture");
      close(client);
      continue;
    }
    child = fork();
    if (child < 0) { perror("fork"); close(client); continue; }
    if (child == 0) {
      char *child_argv[2];
      close(server);
      if (dup2(client, STDIN_FILENO) < 0 || dup2(client, STDOUT_FILENO) < 0) {
        perror("dup2");
        _exit(1);
      }
      if (client > STDOUT_FILENO) close(client);
      child_argv[0] = argv[0];
      child_argv[1] = NULL;
      (void)setenv("LEAFNODE_FAST_EXIT", "1", 1);
      (void)leafnode_nntpd_main(1, child_argv);
      _exit(0);
    }
    close(client);
  }
  (void)argc;
  return 0;
}
