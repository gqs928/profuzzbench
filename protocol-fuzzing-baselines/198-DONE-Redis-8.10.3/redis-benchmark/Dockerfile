FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j2
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG AFLNET_REF=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG REDIS_REF=8.10.3
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG REDIS_ARCHIVE_SHA256=edde778f6bdee7581e42fc139ca9e07e2822212092f7501f99989656e3629d02

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
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
      build-essential ca-certificates clang gcovr git graphviz graphviz-dev \
      llvm llvm-dev make netcat-openbsd pkg-config procps python3 strace \
      && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=ubuntu:ubuntu redis-8.10.3.tar.gz /tmp/redis.tar.gz
COPY --chown=ubuntu:ubuntu aflnet-redis.patch redis_aflnet.c parser-test.c /tmp/

RUN set -eu; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    echo "${REDIS_ARCHIVE_SHA256}  /tmp/redis.tar.gz" | sha256sum -c -; \
    mkdir -p "${AFLNET}" /tmp/redis-src; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    tar -xzf /tmp/redis.tar.gz -C /tmp/redis-src --strip-components=1; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h \
      "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c \
      "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/redis_aflnet.c "${AFLNET}/redis_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-redis.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-redis.patch; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    make -C "${AFLNET}" all "${make_args[@]}"; \
    make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c \
      "${AFLNET}/redis_aflnet.o" -o /tmp/parser-test; \
    /tmp/parser-test

COPY --chown=ubuntu:ubuntu prepare_seeds.py redis.dict redis.conf clean.sh /home/ubuntu/experiments/

RUN set -eu; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    for variant in reference afl gcov; do \
      mkdir -p "${WORKDIR}/redis-${variant}"; \
      cp -a /tmp/redis-src/. "${WORKDIR}/redis-${variant}/"; \
    done; \
    make -C "${WORKDIR}/redis-reference/src" redis-server \
      "${make_args[@]}" REDIS_CFLAGS=-D__STDC_NO_ATOMICS__ \
      USE_JEMALLOC=no BUILD_TLS=no USE_SYSTEMD=no; \
    AFL_USE_ASAN=1 make -C "${WORKDIR}/redis-afl/src" redis-server \
      "${make_args[@]}" CC="${AFLNET}/afl-clang-fast" SANITIZER=address \
      REDIS_CFLAGS=-D__STDC_NO_ATOMICS__ \
      USE_JEMALLOC=no BUILD_TLS=no USE_SYSTEMD=no; \
    make -C "${WORKDIR}/redis-gcov/src" redis-server \
      "${make_args[@]}" CC=cc OPTIMIZATION=-O0 \
      REDIS_CFLAGS="-O0 --coverage -D__STDC_NO_ATOMICS__" REDIS_LDFLAGS=--coverage \
      USE_JEMALLOC=no BUILD_TLS=no USE_SYSTEMD=no; \
    test -x "${WORKDIR}/redis-reference/src/redis-server"; \
    test -x "${WORKDIR}/redis-afl/src/redis-server"; \
    test -x "${WORKDIR}/redis-gcov/src/redis-server"; \
    nm "${WORKDIR}/redis-afl/src/redis-server" | grep -F '__afl_area_ptr' >/dev/null; \
    mkdir -p "${WORKDIR}/in-redis"; \
    python3 "${WORKDIR}/prepare_seeds.py" "${WORKDIR}/in-redis"; \
    { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'aflnet_commit=%s\n' "${AFLNET_REF}"; \
      printf 'redis_version=%s\n' "${REDIS_REF}"; \
      printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'redis_archive_sha256=%s\n' "${REDIS_ARCHIVE_SHA256}"; \
      printf 'aflnet_redis_patch_sha256='; sha256sum /tmp/aflnet-redis.patch | cut -d ' ' -f1; \
      printf 'redis_parser_sha256='; sha256sum /tmp/redis_aflnet.c | cut -d ' ' -f1; \
      printf 'parser_test_sha256='; sha256sum /tmp/parser-test.c | cut -d ' ' -f1; \
      cc --version | sed -n '1p'; \
      clang --version | sed -n '1p'; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' build-essential clang gcovr graphviz llvm llvm-dev make python3; \
    } > "${WORKDIR}/build-versions.txt"

ENV PATH=/home/ubuntu/aflnet:${PATH} \
    REDIS_REFERENCE_BIN=/home/ubuntu/experiments/redis-reference/src/redis-server \
    REDIS_AFL_BIN=/home/ubuntu/experiments/redis-afl/src/redis-server \
    REDIS_GCOV_BIN=/home/ubuntu/experiments/redis-gcov/src/redis-server

EXPOSE 6379/tcp
