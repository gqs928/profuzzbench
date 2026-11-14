/* AFLNet ELF entrypoint; exec the exact-version Redpanda startup/reset script. */
#include <stdio.h>
#include <unistd.h>

int main(void)
{
  char *const args[] = {
    "/bin/bash",
    "/home/redpanda/benchmark/start-redpanda.sh",
    NULL
  };
  execv(args[0], args);
  perror("exec start-redpanda.sh");
  return 127;
}
