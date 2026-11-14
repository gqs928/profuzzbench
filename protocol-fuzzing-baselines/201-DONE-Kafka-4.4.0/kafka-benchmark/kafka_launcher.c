/* AFLNet 要求目标是 ELF；此启动器原进程执行脚本以保留进程号和共享内存。 */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv)
{
  char **child_argv = calloc((size_t)argc + 2U, sizeof(*child_argv));
  int index;

  if (!child_argv) {
    perror("分配 Kafka 启动参数失败");
    return 127;
  }

  child_argv[0] = "/bin/bash";
  child_argv[1] = "/home/ubuntu/experiments/start-kafka.sh";
  for (index = 1; index < argc; index++) child_argv[index + 1] = argv[index];
  execv(child_argv[0], child_argv);

  perror("执行 Kafka 状态复位启动脚本失败");
  free(child_argv);
  return 127;
}
