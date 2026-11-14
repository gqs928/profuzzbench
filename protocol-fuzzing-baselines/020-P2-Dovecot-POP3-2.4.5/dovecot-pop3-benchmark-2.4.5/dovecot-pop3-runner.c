#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static volatile sig_atomic_t server_pgid = -1;

static void forward_signal(int signal_number)
{
    sig_atomic_t pgid = server_pgid;
    if (pgid > 0)
        (void)kill(-(pid_t)pgid, signal_number);
}

int main(void)
{
    const char *prefix = getenv("DOVECOT_AFL_PREFIX");
    const char *config = getenv("DOVECOT_CONFIG");
    char dovecot[1024];
    pid_t child;
    pid_t waited;
    int status;

    if (prefix == NULL || *prefix == '\0')
        prefix = "/home/ubuntu/experiments/dovecot-afl";
    if (config == NULL || *config == '\0')
        config = "/workspace/dovecot.conf";
    if (snprintf(dovecot, sizeof(dovecot), "%s/sbin/dovecot", prefix) >=
        (int)sizeof(dovecot)) {
        fputs("Dovecot installation prefix is too long\n", stderr);
        return 2;
    }

    if (signal(SIGINT, forward_signal) == SIG_ERR ||
        signal(SIGTERM, forward_signal) == SIG_ERR) {
        perror("install signal handler");
        return 2;
    }
    child = fork();
    if (child < 0) {
        perror("fork Dovecot server");
        return 2;
    }
    if (child == 0) {
        (void)setpgid(0, 0);
        (void)prctl(PR_SET_PDEATHSIG, SIGTERM);
        /* Keep AFLNet's outer forkserver; Dovecot and its workers still
           inherit the coverage map through __AFL_SHM_ID. */
        (void)close(198);
        (void)close(199);
        execl(dovecot, dovecot, "-F", "-c", config, (char *)NULL);
        perror("exec Dovecot");
        _exit(127);
    }
    server_pgid = child;
    (void)setpgid(child, child);

    do {
        waited = waitpid(child, &status, 0);
    } while (waited < 0 && errno == EINTR);
    server_pgid = -1;
    if (waited < 0) {
        perror("wait for Dovecot server");
        return 2;
    }
    if (WIFEXITED(status))
        return WEXITSTATUS(status);
    if (WIFSIGNALED(status))
        return 128 + WTERMSIG(status);
    return 1;
}
