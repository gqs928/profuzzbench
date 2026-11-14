FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j1
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG AFLNET_REF=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG MOSQUITTO_VERSION=2.1.2
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG MOSQUITTO_ARCHIVE_SHA256=fd905380691ac65ea5a93779e8214941829e3d6e038d5edff9eac5fd74cbed02

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Bootstrap CA roots before switching Ubuntu mirrors to the dated snapshot.
# BuildKit caches package indexes and downloads; retries handle transient 5xxs.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake build-essential ca-certificates clang gcovr git gdb \
      graphviz graphviz-dev libcjson-dev libaio-dev libevent-dev libssl-dev libtool llvm \
      llvm-dev make net-tools netcat-openbsd pkg-config procps python3 strace \
      zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=ubuntu:ubuntu mosquitto-2.1.2.tar.gz /tmp/mosquitto.tar.gz
COPY --chown=ubuntu:ubuntu aflnet-mqtt.patch mqtt_aflnet.c parser-test.c /tmp/

RUN set -eu; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    echo "${MOSQUITTO_ARCHIVE_SHA256}  /tmp/mosquitto.tar.gz" | sha256sum -c -; \
    mkdir -p "${AFLNET}" /tmp/mosquitto-src; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    tar -xzf /tmp/mosquitto.tar.gz -C /tmp/mosquitto-src --strip-components=1; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h \
      "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c \
      "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/mqtt_aflnet.c "${AFLNET}/mqtt_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-mqtt.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-mqtt.patch; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    make -C "${AFLNET}" all "${make_args[@]}"; \
    make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c \
      "${AFLNET}/mqtt_aflnet.o" -o /tmp/parser-test; \
    /tmp/parser-test

COPY --chown=ubuntu:ubuntu mqtt_packets.py prepare_seeds.py mqtt.dict mosquitto.conf clean.sh /home/ubuntu/experiments/
COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/seeds/

RUN set -eu; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    mkdir -p "${WORKDIR}"; \
    for variant in reference afl gcov; do \
      mkdir -p "${WORKDIR}/mosquitto-${variant}"; \
      cp -a /tmp/mosquitto-src/. "${WORKDIR}/mosquitto-${variant}/"; \
    done; \
    base_args=(WITH_TLS=yes WITH_TLS_PSK=no WITH_DOCS=no WITH_CJSON=yes WITH_HTTP_API=no \
      WITH_WEBSOCKETS=no WITH_SYSTEMD=no WITH_SRV=no \
      WITH_SHARED_LIBRARIES=yes WITH_STATIC_LIBRARIES=no \
      WITH_BUNDLED_DEPS=yes WITH_UNIX_SOCKETS=no); \
    make -C "${WORKDIR}/mosquitto-reference" DIRS="libcommon lib src" \
      "${make_args[@]}" mosquitto "${base_args[@]}" WITH_ASAN=no WITH_COVERAGE=no; \
    AFL_USE_ASAN=1 make -C "${WORKDIR}/mosquitto-afl" DIRS="libcommon lib src" \
      "${make_args[@]}" CC="${AFLNET}/afl-clang-fast" mosquitto \
      "${base_args[@]}" WITH_ASAN=yes WITH_COVERAGE=no; \
    CC=cc make -C "${WORKDIR}/mosquitto-gcov" DIRS="libcommon lib src" \
      "${make_args[@]}" mosquitto "${base_args[@]}" WITH_ASAN=no WITH_COVERAGE=yes; \
    test -x "${WORKDIR}/mosquitto-reference/src/mosquitto"; \
    test -x "${WORKDIR}/mosquitto-afl/src/mosquitto"; \
    test -x "${WORKDIR}/mosquitto-gcov/src/mosquitto"; \
    nm "${WORKDIR}/mosquitto-afl/src/mosquitto" | \
      grep -F '__afl_area_ptr' >/dev/null; \
    mkdir -p "${WORKDIR}/in-mqtt"; \
    python3 "${WORKDIR}/prepare_seeds.py" "${WORKDIR}/seeds" "${WORKDIR}/in-mqtt"; \
    { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'aflnet_commit=%s\n' "${AFLNET_REF}"; \
      printf 'mosquitto_version=%s\n' "${MOSQUITTO_VERSION}"; \
      printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'mosquitto_archive_sha256=%s\n' "${MOSQUITTO_ARCHIVE_SHA256}"; \
      printf 'mosquitto_source_url=https://mosquitto.org/files/source/mosquitto-%s.tar.gz\n' "${MOSQUITTO_VERSION}"; \
      printf 'aflnet_mqtt_patch_sha256='; sha256sum /tmp/aflnet-mqtt.patch | cut -d ' ' -f1; \
      printf 'mqtt_parser_sha256='; sha256sum /tmp/mqtt_aflnet.c | cut -d ' ' -f1; \
      printf 'parser_test_sha256='; sha256sum /tmp/parser-test.c | cut -d ' ' -f1; \
      cc --version | sed -n '1p'; \
      clang --version | sed -n '1p'; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' build-essential clang git llvm llvm-dev make python3; \
    } > "${WORKDIR}/build-versions.txt"

ENV PATH=/home/ubuntu/aflnet:${PATH} \
    MOSQUITTO_REFERENCE_BIN=/home/ubuntu/experiments/mosquitto-reference/src/mosquitto \
    MOSQUITTO_AFL_BIN=/home/ubuntu/experiments/mosquitto-afl/src/mosquitto \
    MOSQUITTO_GCOV_BIN=/home/ubuntu/experiments/mosquitto-gcov/src/mosquitto

EXPOSE 1883/tcp
