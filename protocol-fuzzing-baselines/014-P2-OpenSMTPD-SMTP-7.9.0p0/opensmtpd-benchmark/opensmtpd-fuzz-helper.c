#define _GNU_SOURCE
#include <signal.h>
#include <string.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;
static void request_stop(int sig) { (void)sig; stop_requested = 1; }

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = request_stop;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGTERM, &sa, NULL) != 0 || sigaction(SIGINT, &sa, NULL) != 0) return 2;
    while (!stop_requested) pause();
    return 0;
}
