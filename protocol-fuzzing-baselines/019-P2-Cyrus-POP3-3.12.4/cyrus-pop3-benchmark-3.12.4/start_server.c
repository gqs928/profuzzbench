#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

static int run_restore(void)
{
    int rc = system("/workspace/restore-state.sh");
    if (rc != 0) {
        fputs("Could not restore the deterministic Cyrus mailbox state\n", stderr);
        return -1;
    }
    return 0;
}

int main(void)
{
    const char *prefix = getenv("CYRUS_PREFIX");
    char master[1024];
    char path[4096];
    char libpath[2048];
    const char *old_path = getenv("PATH");
    const char *old_libpath = getenv("LD_LIBRARY_PATH");
    pid_t saslauthd;
    int i;

    if (prefix == NULL || *prefix == '\0')
        prefix = "/home/ubuntu/experiments/cyrus-afl";
    if (setsid() < 0 && errno != EPERM) {
        perror("setsid POP3 testcase");
        return 2;
    }
    if (snprintf(master, sizeof(master), "%s/libexec/master", prefix) >=
        (int)sizeof(master) ||
        snprintf(path, sizeof(path), "%s/bin:%s/sbin:%s/libexec:%s", prefix,
                 prefix, prefix, old_path != NULL ? old_path : "") >=
        (int)sizeof(path) ||
        snprintf(libpath, sizeof(libpath), "%s/lib%s%s", prefix,
                 old_libpath != NULL ? ":" : "",
                 old_libpath != NULL ? old_libpath : "") >= (int)sizeof(libpath)) {
        fputs("Cyrus prefix path is too long\n", stderr);
        return 2;
    }
    if (setenv("PATH", path, 1) < 0 || setenv("LD_LIBRARY_PATH", libpath, 1) < 0) {
        perror("setenv Cyrus paths");
        return 2;
    }
    if (run_restore() < 0)
        return 2;

    saslauthd = fork();
    if (saslauthd < 0) {
        perror("fork saslauthd");
        return 2;
    }
    if (saslauthd == 0) {
        /* saslauthd is a helper, not the instrumented target process. */
        close(198);
        close(199);
        execlp("saslauthd", "saslauthd", "-a", "sasldb", "-n", "2", "-m",
               "/tmp/cyrus-benchmark-state/saslauthd", (char *)NULL);
        perror("exec saslauthd");
        _exit(127);
    }
    for (i = 0; i < 100; i++) {
        struct stat st;
        struct timespec delay = {0, 50000000};
        if (stat("/tmp/cyrus-benchmark-state/saslauthd/mux", &st) == 0 &&
            S_ISSOCK(st.st_mode))
            break;
        nanosleep(&delay, NULL);
    }
    if (i == 100) {
        fputs("saslauthd did not create its socket\n", stderr);
        kill(saslauthd, SIGTERM);
        return 2;
    }

    /* Preserve AFLNet's forkserver descriptors across exec into the instrumented master. */
    execl(master, master, "-D", "-C", "/workspace/imapd.conf", "-M",
          "/workspace/cyrus-pop3.services.conf", (char *)NULL);
    perror("exec Cyrus master");
    kill(saslauthd, SIGTERM);
    return 127;
}
