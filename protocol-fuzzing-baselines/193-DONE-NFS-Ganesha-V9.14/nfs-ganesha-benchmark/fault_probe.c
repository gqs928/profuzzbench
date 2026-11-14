#define _POSIX_C_SOURCE 200809L

#include <arpa/inet.h>
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define RECORD_LIMIT (1024U * 1024U)

/* 网络字节序读取 RPC 头字段，避免主机端序影响探针触发条件。 */
static uint32_t read_u32(const unsigned char *data)
{
	return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) |
	       ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

/* 完整读取请求字节，明确处理 TCP 的部分读。 */
static int read_all(int fd, unsigned char *data, size_t length)
{
	size_t received = 0;
	while (received < length) {
		ssize_t count = recv(fd, data + received, length - received, 0);
		if (count == 0)
			return 0;
		if (count < 0) {
			if (errno == EINTR)
				continue;
			return -1;
		}
		received += (size_t)count;
	}
	return 1;
}

/* 对无故障的 RPC 调用回复 PROG_UNAVAIL，让状态解析器收到有效响应。 */
static void reply_unavailable(int client, uint32_t xid)
{
	unsigned char reply[28] = {
		0x80, 0, 0, 0x18,
		0, 0, 0, 0, /* XID 在运行时写入。 */
		0, 0, 0, 1,
		0, 0, 0, 0,
		0, 0, 0, 0,
		0, 0, 0, 0,
		0, 0, 0, 1,
	};
	reply[4] = (unsigned char)(xid >> 24);
	reply[5] = (unsigned char)(xid >> 16);
	reply[6] = (unsigned char)(xid >> 8);
	reply[7] = (unsigned char)xid;
	(void)send(client, reply, sizeof(reply), MSG_NOSIGNAL);
}

int main(int argc, char **argv)
{
	int listener;
	int client;
	int enabled = 1;
	unsigned int port = argc > 1 ? (unsigned int)strtoul(argv[1], NULL, 10) : 12059U;
	struct sockaddr_in address;
	unsigned char marker[4];
	unsigned char *payload;
	int result;

	signal(SIGPIPE, SIG_IGN);
	listener = socket(AF_INET, SOCK_STREAM, 0);
	if (listener < 0) {
		perror("socket");
		return 2;
	}
	setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &enabled, sizeof(enabled));
	memset(&address, 0, sizeof(address));
	address.sin_family = AF_INET;
	address.sin_port = htons((uint16_t)port);
	address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	if (bind(listener, (struct sockaddr *)&address, sizeof(address)) != 0 ||
	    listen(listener, 4) != 0) {
		perror("bind/listen");
		close(listener);
		return 2;
	}
	fprintf(stderr, "FAULT-PROBE: TCP/%u 等待 NFSv3 RPC 请求\n", port);
	fflush(stderr);
	client = accept(listener, NULL, NULL);
	if (client < 0) {
		perror("accept");
		close(listener);
		return 2;
	}
	result = read_all(client, marker, sizeof(marker));
	if (result == 1) {
		uint32_t length = read_u32(marker) & 0x7fffffffU;
		if (length < 24U || length > RECORD_LIMIT) {
			fprintf(stderr, "FAULT-PROBE: 忽略无效的 RPC 长度 %u\n", length);
		} else {
			payload = (unsigned char *)malloc(length);
			if (!payload) {
				close(client);
				close(listener);
				return 2;
			}
			result = read_all(client, payload, length);
			if (result == 1) {
				uint32_t xid = read_u32(payload);
				uint32_t program = read_u32(payload + 12U);
				uint32_t version = read_u32(payload + 16U);
				uint32_t procedure = read_u32(payload + 20U);
				if (xid == 0U && read_u32(payload + 4U) == 0U && program == 100003U &&
				    version == 3U && procedure == 0U) {
					fprintf(stderr, "FAULT-PROBE: 变异后的 NFSv3 NULL 调用触发 SIGABRT\n");
					fflush(stderr);
					abort();
				}
				reply_unavailable(client, xid);
			}
			free(payload);
		}
	}
	close(client);
	close(listener);
	return 0;
}
