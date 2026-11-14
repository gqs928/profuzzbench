#define _POSIX_C_SOURCE 200809L

#include <arpa/inet.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

int main(void)
{
  static const char greeting[] = "* OK isolated fault probe\r\n";
  static const char reply[] = "A001 OK probe alive\r\n";
  int listener;
  struct sockaddr_in address;
  int reuse = 1;

  listener = socket(AF_INET, SOCK_STREAM, 0);
  if (listener < 0) {
    perror("创建探针监听套接字失败");
    return 2;
  }
  if (setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
    perror("设置探针套接字失败");
    close(listener);
    return 2;
  }

  memset(&address, 0, sizeof(address));
  address.sin_family = AF_INET;
  address.sin_port = htons(1144);
  address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  if (bind(listener, (struct sockaddr *)&address, sizeof(address)) < 0 ||
      listen(listener, 8) < 0) {
    perror("启动探针监听失败");
    close(listener);
    return 2;
  }

  for (;;) {
    int client = accept(listener, NULL, NULL);
    if (client < 0) {
      if (errno == EINTR) continue;
      perror("接受探针连接失败");
      close(listener);
      return 2;
    }
    if (send(client, greeting, sizeof(greeting) - 1U, 0) < 0) {
      close(client);
      continue;
    }
    for (;;) {
      char buffer[4096];
      ssize_t size = recv(client, buffer, sizeof(buffer) - 1U, 0);
      if (size <= 0) break;
      buffer[size] = '\0';
      if (strstr(buffer, "X-FAULT-PROBE") != NULL) {
        /* 此独立服务只验证 AFLNet 的异常记录，不与 Dovecot 链接。 */
        raise(SIGABRT);
      }
      (void)send(client, reply, sizeof(reply) - 1U, 0);
    }
    close(client);
  }
}
