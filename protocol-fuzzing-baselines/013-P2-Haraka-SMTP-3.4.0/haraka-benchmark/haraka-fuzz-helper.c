#define _GNU_SOURCE
#include <signal.h>
#include <string.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;
static void stop(int sig) { (void)sig; stop_requested = 1; }

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = stop;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGTERM, &sa, NULL) || sigaction(SIGINT, &sa, NULL)) return 2;
    while (!stop_requested) pause();
    return 0;
}
