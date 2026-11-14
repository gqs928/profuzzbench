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

# Bootstrap CA roots before switching Ubuntu mirrors to the dated snapshot.
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
      liblmdb-dev libpcre2-dev libsqlite3-dev libssl-dev libsasl2-dev \
      libsasl2-modules libtool libwrap0-dev llvm llvm-dev make netcat-openbsd \
      pkg-config procps python3 python3-minimal sasl2-bin zlib1g-dev \
      && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu && \
    printf 'resp-benchmark-pass\n' | saslpasswd2 -p -c -f /etc/sasldb2 -u localhost fuzzuser && \
    printf 'resp-benchmark-pass\n' | saslpasswd2 -p -c -f /etc/sasldb2 -u localhost cyrusfuzz && \
    chown ubuntu:ubuntu /etc/sasldb2 && chmod 600 /etc/sasldb2

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=ubuntu:ubuntu cyrus-imap-3.12.4.tar.gz /tmp/cyrus.tar.gz
COPY --chown=ubuntu:ubuntu aflnet-imap.patch imap_aflnet.c parser-test.c /tmp/
COPY --chown=ubuntu:ubuntu prepare_seeds.py imap.dict imapd.conf cyrus.conf clean.sh start-server.sh start_server.c /home/ubuntu/experiments/

RUN set -eu; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    echo "${CYRUS_ARCHIVE_SHA256}  /tmp/cyrus.tar.gz" | sha256sum -c -; \
    mkdir -p "${AFLNET}" /tmp/cyrus-src; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    tar -xzf /tmp/cyrus.tar.gz -C /tmp/cyrus-src --strip-components=1; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h \
      "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c \
      "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/imap_aflnet.c "${AFLNET}/imap_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-imap.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-imap.patch; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    make -C "${AFLNET}" all "${make_args[@]}"; \
    make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c \
      "${AFLNET}/imap_aflnet.o" -o /tmp/parser-test; \
    /tmp/parser-test; \
    mkdir -p "${WORKDIR}" "${WORKDIR}/in-imap"; \
    python3 "${WORKDIR}/prepare_seeds.py" "${WORKDIR}/in-imap"; \
    cc -O2 -Wall -Wextra -Werror "${WORKDIR}/start_server.c" \
      -o "${WORKDIR}/start_server"; \
    for variant in reference afl gcov; do \
      mkdir -p "${WORKDIR}/cyrus-${variant}"; \
      cp -a /tmp/cyrus-src/. "${WORKDIR}/cyrus-${variant}/"; \
    done; \
    configure_args=(--with-cyrus-user=ubuntu --with-openssl=/usr \
      --with-sqlite=yes \
      --with-sasl=/usr --with-zlib=/usr --disable-sieve --disable-http \
      --disable-nntp --disable-murder --disable-replication); \
    cd "${WORKDIR}/cyrus-reference"; \
    CC=cc CFLAGS='-O2 -g' ./configure --prefix="${WORKDIR}/cyrus-reference" \
      --sysconfdir="${WORKDIR}/cyrus-reference/etc" \
      --localstatedir="${WORKDIR}/cyrus-reference/var" "${configure_args[@]}"; \
    make "${make_args[@]}"; make install; \
    cd "${WORKDIR}/cyrus-afl"; \
    AFL_USE_ASAN=1 CC="${AFLNET}/afl-clang-fast" CFLAGS='-O1 -g -fno-omit-frame-pointer' \
      ./configure --prefix="${WORKDIR}/cyrus-afl" \
      --sysconfdir="${WORKDIR}/cyrus-afl/etc" \
      --localstatedir="${WORKDIR}/cyrus-afl/var" "${configure_args[@]}"; \
    AFL_USE_ASAN=1 make "${make_args[@]}"; make install; \
    cd "${WORKDIR}/cyrus-gcov"; \
    CC=cc CFLAGS='-O0 -g --coverage' LDFLAGS='--coverage' \
      ./configure --prefix="${WORKDIR}/cyrus-gcov" \
      --sysconfdir="${WORKDIR}/cyrus-gcov/etc" \
      --localstatedir="${WORKDIR}/cyrus-gcov/var" "${configure_args[@]}"; \
    make "${make_args[@]}"; make install; \
    test -x "${WORKDIR}/cyrus-reference/libexec/master"; \
    test -x "${WORKDIR}/cyrus-afl/libexec/imapd"; \
    test -x "${WORKDIR}/cyrus-gcov/libexec/imapd"; \
    { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'aflnet_commit=%s\n' "${AFLNET_REF}"; \
      printf 'cyrus_release=%s\n' "${CYRUS_REF}"; \
      printf 'cyrus_version=%s\n' "$(cat /tmp/cyrus-src/VERSION)"; \
      printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'cyrus_archive_sha256=%s\n' "${CYRUS_ARCHIVE_SHA256}"; \
      printf 'aflnet_imap_patch_sha256='; sha256sum /tmp/aflnet-imap.patch | cut -d ' ' -f1; \
      printf 'imap_parser_sha256='; sha256sum /tmp/imap_aflnet.c | cut -d ' ' -f1; \
      printf 'parser_test_sha256='; sha256sum /tmp/parser-test.c | cut -d ' ' -f1; \
      printf 'launcher_sha256='; sha256sum "${WORKDIR}/start_server.c" | cut -d ' ' -f1; \
      cc --version | sed -n '1p'; clang --version | sed -n '1p'; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' build-essential clang gcovr \
        llvm llvm-dev libsasl2-dev make python3; \
    } > "${WORKDIR}/build-versions.txt"

RUN AFL_USE_ASAN=1 "${AFLNET}/afl-clang-fast" -O1 -g \
      -fno-omit-frame-pointer "${WORKDIR}/start_server.c" \
      -o "${WORKDIR}/start_server"

ENV PATH=/home/ubuntu/aflnet:/home/ubuntu/experiments/cyrus-reference/bin:${PATH} \
    CYRUS_REFERENCE_PREFIX=/home/ubuntu/experiments/cyrus-reference \
    CYRUS_AFL_PREFIX=/home/ubuntu/experiments/cyrus-afl \
    CYRUS_GCOV_PREFIX=/home/ubuntu/experiments/cyrus-gcov \
    IMAP_PORT=1143

EXPOSE 1143/tcp
