#include <arpa/inet.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void) {
  int fd = socket(AF_INET, SOCK_STREAM, 0);
  if (fd < 0) return 1;

  struct sockaddr_in address;
  memset(&address, 0, sizeof(address));
  address.sin_family = AF_INET;
  address.sin_port = htons(3389);
  if (inet_pton(AF_INET, "127.0.0.1", &address.sin_addr) != 1) {
    close(fd);
    return 1;
  }

  if (connect(fd, (struct sockaddr *)&address, sizeof(address)) != 0) {
    fprintf(stderr, "LDAP target is not ready: %s\n", strerror(errno));
    close(fd);
    return 1;
  }
  close(fd);
  return 0;
}
