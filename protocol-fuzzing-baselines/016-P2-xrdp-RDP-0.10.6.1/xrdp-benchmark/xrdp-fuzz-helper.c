#define _GNU_SOURCE
#include <signal.h>
#include <string.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;

static void request_stop(int sig) {
    (void)sig;
    stop_requested = 1;
}

int main(void) {
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = request_stop;
    sigemptyset(&action.sa_mask);
    if (sigaction(SIGTERM, &action, NULL) != 0 || sigaction(SIGINT, &action, NULL) != 0) {
        return 2;
    }
    while (!stop_requested) {
        pause();
    }
    return 0;
}
