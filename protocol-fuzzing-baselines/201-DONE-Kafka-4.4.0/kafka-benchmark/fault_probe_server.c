/* 仅用于校验 AFLNet 能发现并保存可重放异常样本的隔离 TCP 探针。 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define PROBE_PORT 19092
#define MAX_FRAME (1024U * 1024U)

static uint32_t read_u32(const unsigned char *buf)
{
  return ((uint32_t)buf[0] << 24) | ((uint32_t)buf[1] << 16) |
         ((uint32_t)buf[2] << 8) | buf[3];
}

static size_t read_frame(int fd, unsigned char *buf, size_t expected)
{
  size_t used = 0;
  while (used < expected) {
    ssize_t amount = read(fd, buf + used, expected - used);
    if (amount <= 0) return used;
    used += (size_t)amount;
  }
  return used;
}

/* 返回最小的 Kafka 响应帧，让 AFLNet 在故障前先记录协议状态。 */
static void send_state_response(int fd)
{
  const unsigned char response[8] = {0, 0, 0, 4, 0, 0, 0, 1};
  size_t sent = 0;
  while (sent < sizeof(response)) {
    ssize_t amount = write(fd, response + sent, sizeof(response) - sent);
    if (amount <= 0) return;
    sent += (size_t)amount;
  }
}

int main(void)
{
  int listener = socket(AF_INET, SOCK_STREAM, 0);
  struct sockaddr_in address;
  int reuse = 1;
  if (listener < 0) return 2;
  (void)setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
  memset(&address, 0, sizeof(address));
  address.sin_family = AF_INET;
  address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  address.sin_port = htons(PROBE_PORT);
  if (bind(listener, (struct sockaddr *)&address, sizeof(address)) != 0 ||
      listen(listener, 1) != 0)
    return 2;

  for (;;) {
    unsigned char buffer[MAX_FRAME + 4U];
    int client = accept(listener, NULL, NULL);
    if (client < 0) continue;
    if (read_frame(client, buffer, 4U) != 4U) {
      close(client);
      continue;
    }
    uint32_t declared = read_u32(buffer);
    if (declared <= MAX_FRAME && declared > 0U) {
      size_t received = read_frame(client, buffer + 4U, declared);
      send_state_response(client);
      if (received >= sizeof("KAFKA-CRASH-PROBE") - 1U &&
          memmem(buffer + 4U, received, "KAFKA-CRASH-PROBE",
                 sizeof("KAFKA-CRASH-PROBE") - 1U) != NULL) {
        (void)shutdown(client, SHUT_WR);
        usleep(100000);
        abort();
      }
    }
    close(client);
  }
}
