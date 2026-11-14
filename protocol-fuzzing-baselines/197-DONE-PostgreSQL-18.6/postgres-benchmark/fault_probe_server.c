#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

/* 返回最小的 PostgreSQL 启动成功响应，让 AFLNet 记录真实协议状态。 */
static int
read_exact(int client, unsigned char *buffer, size_t size)
{
    size_t received = 0;

    while (received < size)
    {
        ssize_t count = read(client, buffer + received, size - received);
        if (count < 0)
        {
            if (errno == EINTR)
                continue;
            return -1;
        }
        if (count == 0)
            return -1;
        received += (size_t) count;
    }
    return 0;
}

static unsigned int
read_u32(const unsigned char *bytes)
{
    return ((unsigned int) bytes[0] << 24) |
           ((unsigned int) bytes[1] << 16) |
           ((unsigned int) bytes[2] << 8) | (unsigned int) bytes[3];
}

static int
read_request(int client, unsigned char *request, size_t capacity,
             size_t *request_size)
{
    unsigned int length;
    size_t header_size;
    size_t remaining;

    if (read_exact(client, request, 1) != 0)
        return -1;
    if (request[0] == 0)
    {
        header_size = 8;
        if (capacity < header_size || read_exact(client, request + 1, 7) != 0)
            return -1;
        length = read_u32(request);
        if (length < 8 || length > capacity)
            return -1;
        remaining = length - 8U;
    }
    else
    {
        header_size = 5;
        if (capacity < header_size || read_exact(client, request + 1, 4) != 0)
            return -1;
        length = read_u32(request + 1);
        if (length < 4 || length > capacity - 1)
            return -1;
        remaining = length - 4U;
    }
    if (header_size + remaining > capacity ||
        read_exact(client, request + header_size, remaining) != 0)
        return -1;
    *request_size = (size_t) length + (request[0] == 0 ? 0U : 1U);
    return 0;
}

static int
send_ready(int client)
{
    static const unsigned char response[] = {
        'R', 0, 0, 0, 8, 0, 0, 0, 0,
        'Z', 0, 0, 0, 5, 'I'
    };
    size_t sent = 0;

    while (sent < sizeof(response))
    {
        ssize_t count = write(client, response + sent, sizeof(response) - sent);
        if (count < 0)
        {
            if (errno == EINTR)
                continue;
            return -1;
        }
        sent += (size_t) count;
    }
    return 0;
}

/* 为固定的安全查询返回 CommandComplete 和 ReadyForQuery。 */
static int
send_query_success(int client)
{
    static const unsigned char response[] = {
        'C', 0, 0, 0, 13, 'S', 'E', 'L', 'E', 'C', 'T', ' ', '1', 0,
        'Z', 0, 0, 0, 5, 'I'
    };
    size_t sent = 0;

    while (sent < sizeof(response))
    {
        ssize_t count = write(client, response + sent, sizeof(response) - sent);
        if (count < 0)
        {
            if (errno == EINTR)
                continue;
            return -1;
        }
        sent += (size_t) count;
    }
    return 0;
}

int
main(int argc, char **argv)
{
    int listener, client, reuse = 1;
    struct sockaddr_in address;
    unsigned char request[65536];
    static const unsigned char valid_startup[] = {
        0, 0, 0, 8, 0, 3, 0, 0
    };
    size_t received;
    int startup_mutated;
    long port;

    if (argc != 2)
        return 2;
    port = strtol(argv[1], NULL, 10);
    if (port < 1024 || port > 65535)
        return 2;
    listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0)
        return 3;
    (void) setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_port = htons((unsigned short) port);
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(listener, (struct sockaddr *) &address, sizeof(address)) < 0 ||
        listen(listener, 1) < 0)
        return 4;

    client = accept(listener, NULL, NULL);
    if (client < 0)
        return 5;
    if (read_exact(client, request, sizeof(valid_startup)) != 0)
        return 6;
    startup_mutated = memcmp(request, valid_startup, sizeof(valid_startup)) != 0;
    if (send_ready(client) != 0)
        return 6;

    if (read_request(client, request, sizeof(request), &received) == 0 &&
        request[0] == 'Q')
    {
        static const unsigned char safe_query[] = {
            'Q', 0, 0, 0, 13, 'S', 'E', 'L', 'E', 'C', 'T', ' ', '1', 0
        };
        static const char message[] =
            "故障探针：已完成 PostgreSQL 启动握手，现故意触发 SIGABRT\n";

        if (!startup_mutated && received == sizeof(safe_query) &&
            memcmp(request, safe_query, sizeof(safe_query)) == 0)
        {
            (void) send_query_success(client);
            (void) close(client);
            (void) close(listener);
            return 0;
        }
        (void) write(STDERR_FILENO, message, sizeof(message) - 1);
        abort();
    }

    (void) close(client);
    (void) close(listener);
    return 0;
}
