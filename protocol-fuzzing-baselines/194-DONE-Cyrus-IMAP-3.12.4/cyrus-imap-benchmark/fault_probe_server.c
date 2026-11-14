/* Separate test fixture for verifying AFLNet crash observability.
 * This is never linked into or patched into Cyrus. */
#define _POSIX_C_SOURCE 200809L

#include <arpa/inet.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static int contains_fault_token(const unsigned char *data, size_t length)
{
    /* The fixed seed begins with 'A'. AFL's first one-bit flip changes it to
     * '@', giving this controlled probe a deterministic, fast trigger. */
    return length > 0 && data[0] == '@';
}

int main(void)
{
    static const char greeting[] = "* OK controlled IMAP probe ready\r\n";
    int listener, client, option = 1;
    struct sockaddr_in address;
    unsigned char buffer[65536];
    ssize_t count;

    listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0) return 2;
    setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &option, sizeof(option));
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = htons(1144);
    if (bind(listener, (struct sockaddr *)&address, sizeof(address)) < 0 ||
        listen(listener, 1) < 0)
        return 2;
    client = accept(listener, NULL, NULL);
    if (client < 0) return 2;
    (void)write(client, greeting, sizeof(greeting) - 1);

    while ((count = read(client, buffer, sizeof(buffer))) > 0) {
        size_t start = 0;
        if (contains_fault_token(buffer, (size_t)count)) {
            (void)write(STDERR_FILENO, "CONTROLLED_FAULT_TRIGGERED\n", 27);
            raise(SIGSEGV);
            _exit(139);
        }
        while (start < (size_t)count) {
            size_t end = start;
            char tag[64];
            size_t tag_length;
            char response[128];
            while (end + 1 < (size_t)count &&
                   !(buffer[end] == '\r' && buffer[end + 1] == '\n'))
                end++;
            if (end + 1 >= (size_t)count) break;
            tag_length = 0;
            while (start + tag_length < end && buffer[start + tag_length] != ' ' &&
                   tag_length + 1 < sizeof(tag))
                tag_length++;
            if (tag_length == 0) tag_length = 1;
            memcpy(tag, buffer + start, tag_length);
            tag[tag_length] = '\0';
            (void)snprintf(response, sizeof(response), "%s OK Completed\r\n", tag);
            (void)write(client, response, strlen(response));
            start = end + 2;
        }
    }
    close(client);
    close(listener);
    return 0;
}
