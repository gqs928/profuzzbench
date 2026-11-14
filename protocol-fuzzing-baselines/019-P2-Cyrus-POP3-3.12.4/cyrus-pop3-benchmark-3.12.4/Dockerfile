FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j2
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG AFLNET_REF=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG CYRUS_REF=cyrus-imapd-3.12.4
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG CYRUS_ARCHIVE_SHA256=87a39e27208d9019f00608483d532eb05bd0d71394a6f3f8bb05a72833ad8d91

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    SASL_DBNAME=/etc/sasldb2 \
    ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake bison build-essential ca-certificates clang flex gcovr git \
      graphviz graphviz-dev libical-dev libicu-dev libjansson-dev libkrb5-dev libldap2-dev \
      liblmdb-dev libpcre2-dev libsqlite3-dev libssl-dev libsasl2-dev libsasl2-modules \
      libtool libwrap0-dev llvm llvm-dev make netcat-openbsd pkg-config procps \
      python3 python3-minimal sasl2-bin zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu && \
    printf 'resp-benchmark-pass\n' | saslpasswd2 -p -c -f /etc/sasldb2 -u localhost fuzzuser && \
    printf 'resp-benchmark-pass\n' | saslpasswd2 -p -c -f /etc/sasldb2 -u localhost cyrusfuzz && \
    chown ubuntu:ubuntu /etc/sasldb2 && chmod 600 /etc/sasldb2

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY --chown=ubuntu:ubuntu source/cyrus-imap-3.12.4.tar.gz /tmp/source/cyrus-imap-3.12.4.tar.gz
COPY --chown=ubuntu:ubuntu source-checksums.sha256 /tmp/source-checksums.sha256
COPY --chown=ubuntu:ubuntu aflnet-pop3.patch pop3_aflnet.c parser-test.c pop3.dict prepare_seeds.py /tmp/
COPY --chown=ubuntu:ubuntu imapd.conf cyrus-pop3.services.conf cyrus-imap-bootstrap.conf \
    cyrus-imap-bootstrap.services.conf reset-state.sh restore-state.sh start-imap-bootstrap.sh \
    make-seed-state.sh bootstrap_mailbox.py start_server.c /home/ubuntu/experiments/
COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/in-pop3/
COPY --chown=ubuntu:ubuntu seeds-manifest.json /home/ubuntu/experiments/seeds-manifest.json

RUN set -eu; \
    cd /tmp && sha256sum -c /tmp/source-checksums.sha256; \
    mv /tmp/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz; \
    mv /tmp/source/cyrus-imap-3.12.4.tar.gz /tmp/cyrus.tar.gz; \
    cd /home/ubuntu; \
    mkdir -p "${AFLNET}" /tmp/cyrus-src "${WORKDIR}"; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    tar -xzf /tmp/cyrus.tar.gz -C /tmp/cyrus-src --strip-components=1; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h \
      "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/pop3_aflnet.c "${AFLNET}/pop3_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-pop3.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-pop3.patch; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    make -C "${AFLNET}" all "${make_args[@]}"; \
    make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c \
      "${AFLNET}/pop3_aflnet.o" -o /tmp/parser-test; \
    /tmp/parser-test; \
    python3 /tmp/prepare_seeds.py /tmp/generated-pop3-seeds --username fuzzuser \
      --password resp-benchmark-pass --manifest /tmp/generated-pop3-seeds-manifest.json; \
    diff -r "${WORKDIR}/in-pop3" /tmp/generated-pop3-seeds; \
    cmp "${WORKDIR}/seeds-manifest.json" /tmp/generated-pop3-seeds-manifest.json; \
    cc -O2 -Wall -Wextra -Werror "${WORKDIR}/start_server.c" -o "${WORKDIR}/start_server_reference"; \
    for variant in reference afl gcov; do \
      mkdir -p "${WORKDIR}/cyrus-${variant}"; \
      cp -a /tmp/cyrus-src/. "${WORKDIR}/cyrus-${variant}/"; \
    done; \
    configure_args=(--with-cyrus-user=ubuntu --with-openssl=/usr --with-sqlite=yes \
      --with-sasl=/usr --with-zlib=/usr --disable-sieve --disable-http \
      --disable-nntp --disable-murder --disable-replication); \
    cd "${WORKDIR}/cyrus-reference"; \
    CC=cc CFLAGS='-O2 -g' ./configure --prefix="${WORKDIR}/cyrus-reference" \
      --sysconfdir="${WORKDIR}/cyrus-reference/etc" --localstatedir="${WORKDIR}/cyrus-reference/var" "${configure_args[@]}"; \
    make "${make_args[@]}"; make install; \
    cd "${WORKDIR}/cyrus-afl"; \
    AFL_USE_ASAN=1 CC="${AFLNET}/afl-clang-fast" CFLAGS='-O1 -g -fno-omit-frame-pointer' \
      ./configure --prefix="${WORKDIR}/cyrus-afl" --sysconfdir="${WORKDIR}/cyrus-afl/etc" \
      --localstatedir="${WORKDIR}/cyrus-afl/var" "${configure_args[@]}"; \
    AFL_USE_ASAN=1 make "${make_args[@]}"; make install; \
    cd "${WORKDIR}/cyrus-gcov"; \
    CC=cc CFLAGS='-O0 -g --coverage' LDFLAGS='--coverage' ./configure \
      --prefix="${WORKDIR}/cyrus-gcov" --sysconfdir="${WORKDIR}/cyrus-gcov/etc" \
      --localstatedir="${WORKDIR}/cyrus-gcov/var" "${configure_args[@]}"; \
    make "${make_args[@]}"; make install; \
    test -x "${WORKDIR}/cyrus-reference/libexec/master"; \
    test -x "${WORKDIR}/cyrus-afl/libexec/pop3d"; \
    test -x "${WORKDIR}/cyrus-gcov/libexec/pop3d"; \
    AFL_USE_ASAN=1 "${AFLNET}/afl-clang-fast" -O1 -g -fno-omit-frame-pointer \
      "${WORKDIR}/start_server.c" -o "${WORKDIR}/start_server_afl"; \
    chmod +x "${WORKDIR}"/*.sh; \
    { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'aflnet_commit=%s\n' "${AFLNET_REF}"; \
      printf 'cyrus_release=%s\n' "${CYRUS_REF}"; \
      printf 'cyrus_version=%s\n' "$(cat /tmp/cyrus-src/VERSION)"; \
      printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'cyrus_archive_sha256=%s\n' "${CYRUS_ARCHIVE_SHA256}"; \
      printf 'pop3_patch_sha256='; sha256sum /tmp/aflnet-pop3.patch | cut -d ' ' -f1; \
      printf 'pop3_parser_sha256='; sha256sum /tmp/pop3_aflnet.c | cut -d ' ' -f1; \
      printf 'runner_sha256='; sha256sum "${WORKDIR}/start_server.c" | cut -d ' ' -f1; \
      cc --version | sed -n '1p'; clang --version | sed -n '1p'; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' build-essential clang gcovr llvm llvm-dev libsasl2-dev make python3; \
    } > "${WORKDIR}/build-versions.txt"

RUN set -eu; \
    printf 'resp-benchmark-pass\n' | saslpasswd2 -p -c -f /etc/sasldb2 fuzzuser; \
    printf 'resp-benchmark-pass\n' | saslpasswd2 -p -c -f /etc/sasldb2 cyrusfuzz; \
    "${WORKDIR}/make-seed-state.sh"

ENV PATH=/home/ubuntu/aflnet:/home/ubuntu/experiments/cyrus-reference/bin:${PATH} \
    CYRUS_REFERENCE_PREFIX=/home/ubuntu/experiments/cyrus-reference \
    CYRUS_AFL_PREFIX=/home/ubuntu/experiments/cyrus-afl \
    CYRUS_GCOV_PREFIX=/home/ubuntu/experiments/cyrus-gcov \
    POP3_PORT=1110

EXPOSE 1110/tcp
