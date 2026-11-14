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

static pid_t server_pid = -1;

static void forward_signal(int signal_number)
{
    if (server_pid > 0)
        (void)kill(-server_pid, signal_number);
}

int main(int argc, char **argv)
{
    const char *profile;
    const char *prefix;
    char listener[1024];
    char login[1024];
    char server[1024];
    const char *port;
    pid_t child;
    pid_t waited;
    int status;

    if (argc != 2 || (strcmp(argv[1], "pop3") != 0 &&
                      strcmp(argv[1], "imap") != 0)) {
        fputs("usage: courier-runner pop3|imap\n", stderr);
        return 2;
    }
    profile = argv[1];
    prefix = getenv("COURIER_AFL_PREFIX");
    if (prefix == NULL || *prefix == '\0')
        prefix = "/opt/courier-afl";

    if (snprintf(listener, sizeof(listener), "%s/libexec/couriertcpd", prefix) >=
            (int)sizeof(listener) ||
        snprintf(login, sizeof(login), "%s/sbin/%slogin", prefix,
                 strcmp(profile, "pop3") == 0 ? "pop3" : "imap") >=
            (int)sizeof(login) ||
        snprintf(server, sizeof(server), "%s/bin/%sd", prefix,
                 strcmp(profile, "pop3") == 0 ? "pop3" : "imap") >=
            (int)sizeof(server)) {
        fputs("Courier installation prefix is too long\n", stderr);
        return 2;
    }
    port = strcmp(profile, "pop3") == 0 ? "1110" : "1143";

    if (signal(SIGTERM, forward_signal) == SIG_ERR ||
        signal(SIGINT, forward_signal) == SIG_ERR) {
        perror("install signal handler");
        return 2;
    }
    child = fork();
    if (child < 0) {
        perror("fork Courier listener");
        return 2;
    }
    if (child == 0) {
        (void)setpgid(0, 0);
        (void)prctl(PR_SET_PDEATHSIG, SIGTERM);
        /* AFLNet owns the outer forkserver; nested Courier executables share
           its coverage map but must not start a second forkserver. */
        (void)close(198);
        (void)close(199);
        execl(listener, listener, "-address=127.0.0.1", "-maxprocs=40",
              "-maxperip=40", "-nodnslookup", port, login, server, "Maildir",
              (char *)NULL);
        perror("exec couriertcpd");
        _exit(127);
    }
    server_pid = child;
    (void)setpgid(child, child);

    do {
        waited = waitpid(child, &status, 0);
    } while (waited < 0 && errno == EINTR);
    server_pid = -1;
    if (waited < 0) {
        perror("wait for Courier listener");
        return 2;
    }
    if (WIFEXITED(status))
        return WEXITSTATUS(status);
    if (WIFSIGNALED(status))
        return 128 + WTERMSIG(status);
    return 1;
}
