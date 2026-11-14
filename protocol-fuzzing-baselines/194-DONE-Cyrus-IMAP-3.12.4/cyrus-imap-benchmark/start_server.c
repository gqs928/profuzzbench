#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

static int ensure_dir(const char *path)
{
    if (mkdir(path, 0755) == 0 || errno == EEXIST)
        return 0;
    perror(path);
    return -1;
}

static int prepare_state(void)
{
    const char *dirs[] = {
        "/tmp/cyrus-benchmark-state",
        "/tmp/cyrus-benchmark-state/config",
        "/tmp/cyrus-benchmark-state/config/socket",
        "/tmp/cyrus-benchmark-state/proc",
        "/tmp/cyrus-benchmark-state/lock",
        "/tmp/cyrus-benchmark-state/mail",
        "/tmp/cyrus-benchmark-state/sieve",
        "/tmp/cyrus-benchmark-state/saslauthd",
    };
    size_t i;

    for (i = 0; i < sizeof(dirs) / sizeof(dirs[0]); i++) {
        if (ensure_dir(dirs[i]) < 0)
            return -1;
    }
    return 0;
}

int main(void)
{
    const char *prefix = getenv("CYRUS_PREFIX");
    const char *old_path;
    const char *old_ld_library_path;
    char master[1024];
    char executable_path[4096];
    char library_path[2048];
    pid_t saslauthd;
    int i;

    if (prefix == NULL || *prefix == '\0')
        prefix = "/home/ubuntu/experiments/cyrus-afl";
    /* Cyrus master signals its whole process group during graceful shutdown.
     * Isolate this testcase so AFL's persistent forkserver stays alive. */
    if (setsid() < 0 && errno != EPERM) {
        perror("setsid IMAP testcase");
        return 2;
    }
    if (snprintf(master, sizeof(master), "%s/libexec/master", prefix) >=
        (int)sizeof(master)) {
        fputs("CYRUS_PREFIX path is too long\n", stderr);
        return 2;
    }

    old_path = getenv("PATH");
    old_ld_library_path = getenv("LD_LIBRARY_PATH");
    if (snprintf(executable_path, sizeof(executable_path),
                 "%s/bin:%s/sbin:%s/libexec:%s", prefix, prefix, prefix,
                 old_path != NULL ? old_path : "") >=
            (int)sizeof(executable_path) ||
        snprintf(library_path, sizeof(library_path), "%s/lib%s%s", prefix,
                 old_ld_library_path != NULL ? ":" : "",
                 old_ld_library_path != NULL ? old_ld_library_path : "") >=
            (int)sizeof(library_path)) {
        fputs("CYRUS_PREFIX environment is too long\n", stderr);
        return 2;
    }
    if (setenv("PATH", executable_path, 1) < 0 ||
        setenv("LD_LIBRARY_PATH", library_path, 1) < 0) {
        perror("setenv Cyrus runtime paths");
        return 2;
    }

    if (system("/workspace/reset-state.sh") != 0) {
        fputs("Failed to reset state before IMAP session\n", stderr);
        return 2;
    }
    if (prepare_state() < 0)
        return 2;

    saslauthd = fork();
    if (saslauthd < 0) {
        perror("fork saslauthd");
        return 2;
    }
    if (saslauthd == 0) {
        execlp("saslauthd", "saslauthd", "-a", "sasldb", "-n", "2", "-m",
               "/tmp/cyrus-benchmark-state/saslauthd", (char *)NULL);
        perror("exec saslauthd");
        _exit(127);
    }

    for (i = 0; i < 40; i++) {
        struct stat st;
        struct timespec delay = {0, 50000000};
        if (stat("/tmp/cyrus-benchmark-state/saslauthd/mux", &st) == 0 &&
            S_ISSOCK(st.st_mode))
            break;
        nanosleep(&delay, NULL);
    }
    if (i == 40) {
        fputs("saslauthd did not create its socket\n", stderr);
        return 2;
    }

    execl(master, master, "-D", "-C", "/workspace/imapd.conf", "-M",
          "/workspace/cyrus.conf", (char *)NULL);
    perror("exec Cyrus master");
    return 127;
}
