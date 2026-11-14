#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t shutdown_requested = 0;
static volatile sig_atomic_t postgres_pid = -1;

/* AFLNet 停止当前样本时，同时通知 PostgreSQL 主进程正常关机。 */
static void
forward_shutdown(int signal_number)
{
    (void) signal_number;
    shutdown_requested = 1;
    if (postgres_pid > 0)
        (void) kill((pid_t) postgres_pid, SIGTERM);
}

/* 通过独立客户端检查端口就绪，不把探测请求混入协议会话。 */
static int
probe_readiness(const char *pg_isready, const char *port)
{
    pid_t child = fork();
    int status;

    if (child < 0)
        return -1;
    if (child == 0)
    {
        int null_fd = open("/dev/null", O_WRONLY);
        if (null_fd >= 0)
        {
            (void) dup2(null_fd, STDOUT_FILENO);
            (void) dup2(null_fd, STDERR_FILENO);
            (void) close(null_fd);
        }
        execl(pg_isready, pg_isready, "-h", "127.0.0.1", "-p", port,
              "-U", "postgres", (char *) NULL);
        _exit(127);
    }

    while (waitpid(child, &status, 0) < 0)
    {
        if (errno == EINTR)
            continue;
        return -1;
    }
    return WIFEXITED(status) && WEXITSTATUS(status) == 0;
}

/* 在当前 AFL 目标进程中复位数据库。 */
static int
reset_cluster(const char *clean_script)
{
    pid_t child = fork();
    int status;

    if (child < 0)
    {
        fprintf(stderr, "无法创建 PostgreSQL 集群复位进程：%s\n",
                strerror(errno));
        return -1;
    }
    if (child == 0)
    {
        execl("/bin/bash", "bash", clean_script, (char *) NULL);
        fprintf(stderr, "无法执行 PostgreSQL 集群复位脚本：%s\n",
                strerror(errno));
        _exit(127);
    }

    while (waitpid(child, &status, 0) < 0)
    {
        if (errno == EINTR)
            continue;
        fprintf(stderr, "等待 PostgreSQL 集群复位进程失败：%s\n",
                strerror(errno));
        return -1;
    }
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0)
    {
        fprintf(stderr, "PostgreSQL 集群复位脚本执行失败。\n");
        return -1;
    }
    return 0;
}

int
main(int argc, char **argv)
{
    const char *target = getenv("POSTGRES_AFL_BIN");
    const char *clean_script = getenv("POSTGRES_CLEAN_SCRIPT");
    const char *pg_isready = getenv("POSTGRES_PG_ISREADY_BIN");
    const char *port = getenv("POSTGRES_PORT");
    const char *ready_timeout = getenv("POSTGRES_READY_TIMEOUT_SEC");
    unsigned int timeout_seconds = 10;
    unsigned int elapsed_ms = 0;
    pid_t child;
    int status;
    struct sigaction action;

    if (target == NULL || target[0] == '\0')
        target = "/home/ubuntu/experiments/postgres-afl/bin/postgres";
    if (clean_script == NULL || clean_script[0] == '\0')
        clean_script = "/workspace/clean.sh";
    if (pg_isready == NULL || pg_isready[0] == '\0')
        pg_isready = "/home/ubuntu/experiments/postgres-reference/bin/pg_isready";
    if (port == NULL || port[0] == '\0')
        port = "5432";
    if (ready_timeout != NULL && ready_timeout[0] != '\0')
    {
        char *end = NULL;
        unsigned long parsed = strtoul(ready_timeout, &end, 10);
        if (end != ready_timeout && *end == '\0' && parsed > 0 && parsed <= 60)
            timeout_seconds = (unsigned int) parsed;
    }

    if (access(target, X_OK) != 0)
    {
        fprintf(stderr, "缺少可执行的 AFL 插桩 PostgreSQL：%s\n", target);
        return 2;
    }
    if (access(clean_script, R_OK) != 0)
    {
        fprintf(stderr, "无法读取 PostgreSQL 集群复位脚本：%s\n",
                clean_script);
        return 2;
    }
    if (access(pg_isready, X_OK) != 0)
    {
        fprintf(stderr, "缺少 PostgreSQL 就绪检查程序：%s\n", pg_isready);
        return 2;
    }
    if (reset_cluster(clean_script) != 0)
        return 1;

    child = fork();
    if (child < 0)
    {
        fprintf(stderr, "无法创建 PostgreSQL 服务进程：%s\n", strerror(errno));
        return 1;
    }
    if (child == 0)
    {
        argv[0] = (char *) target;
        execv(target, argv);
        fprintf(stderr, "无法启动 AFL 插桩 PostgreSQL：%s\n", strerror(errno));
        _exit(127);
    }

    postgres_pid = (sig_atomic_t) child;
    memset(&action, 0, sizeof(action));
    action.sa_handler = forward_shutdown;
    sigemptyset(&action.sa_mask);
    if (sigaction(SIGTERM, &action, NULL) != 0 ||
        sigaction(SIGINT, &action, NULL) != 0)
    {
        (void) kill(child, SIGTERM);
        while (waitpid(child, &status, 0) < 0 && errno == EINTR)
            ;
        fprintf(stderr, "无法安装 PostgreSQL 停止信号处理器。\n");
        return 1;
    }

    while (!shutdown_requested && elapsed_ms < timeout_seconds * 1000)
    {
        int ready = probe_readiness(pg_isready, port);
        if (ready == 1)
            break;
        if (ready < 0)
        {
            (void) kill(child, SIGTERM);
            elapsed_ms = timeout_seconds * 1000;
            break;
        }

        struct timespec pause = {0, 100000000L};
        while (nanosleep(&pause, &pause) < 0 && errno == EINTR)
        {
            if (shutdown_requested)
                break;
        }
        elapsed_ms += 100;
    }

    if (shutdown_requested || elapsed_ms >= timeout_seconds * 1000)
    {
        (void) kill(child, SIGTERM);
        if (!shutdown_requested)
            fprintf(stderr, "PostgreSQL 未在 %u 秒内就绪。\n", timeout_seconds);
    }

    while (waitpid(child, &status, 0) < 0)
    {
        if (errno == EINTR)
            continue;
        fprintf(stderr, "等待 PostgreSQL 服务进程失败：%s\n", strerror(errno));
        return 1;
    }

    if (!WIFEXITED(status))
        return 1;
    if (WEXITSTATUS(status) != 0 && !shutdown_requested)
        return WEXITSTATUS(status);
    (void) argc;
    return 0;
}
