#include <stdio.h>
#include <wolfssl/ssl.h>
int main(void) {
    const char *version = wolfSSL_lib_version();
    if (version == NULL) return 1;
    puts(version);
    return 0;
}
