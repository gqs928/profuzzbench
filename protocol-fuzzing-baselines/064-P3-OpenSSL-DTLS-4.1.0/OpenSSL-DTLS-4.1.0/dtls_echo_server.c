#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <netinet/in.h>
#include <openssl/bio.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static void report_ssl_error(const char *where) {
    fprintf(stderr, "%s failed\n", where);
    ERR_print_errors_fp(stderr);
}

static int parse_args(int argc, char **argv, unsigned short *port,
                      const char **cert, const char **key) {
    *port = 20220;
    *cert = "/run/openssl-dtls-benchmark/server.crt";
    *key = "/run/openssl-dtls-benchmark/server.key";
    for (int i = 1; i < argc; ++i) {
        if (i + 1 >= argc) return 0;
        if (strcmp(argv[i], "--port") == 0) {
            char *end = NULL;
            long value = strtol(argv[++i], &end, 10);
            if (!end || *end || value < 1 || value > 65535) return 0;
            *port = (unsigned short)value;
        } else if (strcmp(argv[i], "--cert") == 0) {
            *cert = argv[++i];
        } else if (strcmp(argv[i], "--key") == 0) {
            *key = argv[++i];
        } else {
            return 0;
        }
    }
    return 1;
}

int main(int argc, char **argv) {
    unsigned short port;
    const char *cert_path, *key_path;
    if (!parse_args(argc, argv, &port, &cert_path, &key_path)) {
        fprintf(stderr, "usage: %s [--port 1..65535] [--cert FILE] [--key FILE]\n", argv[0]);
        return 2;
    }

    signal(SIGPIPE, SIG_IGN);
    SSL_CTX *ctx = SSL_CTX_new(DTLS_server_method());
    if (!ctx || !SSL_CTX_set_min_proto_version(ctx, DTLS1_2_VERSION) ||
        !SSL_CTX_set_max_proto_version(ctx, DTLS1_2_VERSION) ||
        !SSL_CTX_use_certificate_file(ctx, cert_path, SSL_FILETYPE_PEM) ||
        !SSL_CTX_use_PrivateKey_file(ctx, key_path, SSL_FILETYPE_PEM) ||
        !SSL_CTX_check_private_key(ctx)) {
        report_ssl_error("OpenSSL DTLS context/certificate setup");
        SSL_CTX_free(ctx);
        return 2;
    }

    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) {
        perror("socket");
        SSL_CTX_free(ctx);
        return 2;
    }
    int reuse = 1;
    (void)setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    struct sockaddr_in local;
    memset(&local, 0, sizeof(local));
    local.sin_family = AF_INET;
    local.sin_port = htons(port);
    local.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(fd, (struct sockaddr *)&local, sizeof(local)) != 0) {
        perror("bind");
        close(fd);
        SSL_CTX_free(ctx);
        return 2;
    }

    BIO *bio = BIO_new_dgram(fd, BIO_NOCLOSE);
    SSL *ssl = SSL_new(ctx);
    if (!bio || !ssl) {
        report_ssl_error("OpenSSL DTLS allocation");
        BIO_free(bio);
        SSL_free(ssl);
        close(fd);
        SSL_CTX_free(ctx);
        return 2;
    }

    /* Peek without consuming the first ClientHello, then connect the bound UDP
       socket to this peer so the datagram BIO stays isolated to one client. */
    struct sockaddr_in peer;
    memset(&peer, 0, sizeof(peer));
    socklen_t peer_len = sizeof(peer);
    unsigned char first_byte;
    ssize_t peeked = recvfrom(fd, &first_byte, sizeof(first_byte), MSG_PEEK,
                              (struct sockaddr *)&peer, &peer_len);
    BIO_ADDR *bio_peer = BIO_ADDR_new();
    if (peeked < 0 || peer.sin_family != AF_INET || !bio_peer ||
        !BIO_ADDR_rawmake(bio_peer, AF_INET, &peer.sin_addr, sizeof(peer.sin_addr),
                          peer.sin_port) ||
        connect(fd, (struct sockaddr *)&peer, peer_len) != 0 ||
        !BIO_ctrl_set_connected(bio, bio_peer)) {
        perror("receive initial DTLS datagram / set peer");
        BIO_ADDR_free(bio_peer);
        SSL_free(ssl);
        BIO_free(bio);
        close(fd);
        SSL_CTX_free(ctx);
        return 0;
    }
    BIO_ADDR_free(bio_peer);

    SSL_set_bio(ssl, bio, bio);
    (void)SSL_set_mtu(ssl, 1200);
    if (SSL_accept(ssl) != 1) {
        report_ssl_error("DTLS 1.2 handshake");
        SSL_free(ssl);
        close(fd);
        SSL_CTX_free(ctx);
        return 0; /* Malformed or incomplete fuzz inputs are not target crashes. */
    }

    unsigned char message[4096];
    int received = SSL_read(ssl, message, sizeof(message));
    if (getenv("OPENSSL_DTLS_DEBUG")) {
        fprintf(stderr, "SSL_read returned %d (error=%d)\n", received,
                received > 0 ? SSL_ERROR_NONE : SSL_get_error(ssl, received));
    }
    if (received > 0) {
        for (int left = 0, right = received - 1; left < right; ++left, --right) {
            unsigned char tmp = message[left];
            message[left] = message[right];
            message[right] = tmp;
        }
        int sent = 0;
        while (sent < received) {
            int n = SSL_write(ssl, message + sent, received - sent);
            if (getenv("OPENSSL_DTLS_DEBUG"))
                fprintf(stderr, "SSL_write returned %d for %d bytes\n", n, received - sent);
            if (n <= 0) break;
            sent += n;
        }
    }

    (void)SSL_shutdown(ssl);
    SSL_free(ssl);
    close(fd);
    SSL_CTX_free(ctx);
    return 0;
}
