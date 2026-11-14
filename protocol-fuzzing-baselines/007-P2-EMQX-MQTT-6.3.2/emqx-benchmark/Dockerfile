ARG BUILDER_IMAGE=ghcr.io/emqx/emqx-builder/6.2-3:1.19.1-28.4.1-7-ubuntu24.04@sha256:7134ef634abc6021f100c2a16cb83b40fed2a44671037ba2d25ca0c0fa21d12d
FROM ${BUILDER_IMAGE}

ARG MAKE_JOBS=2
ARG EMQX_ARCHIVE_SHA256=9102f802386677433487b5d66515e74956ce1fcea8c1454fada6f23383df9143
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG EMQX_COMMIT=6e4ee3d080865d163e91f3e202c6c2d125523b3c

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    ERL_FLAGS="+S 4:4 +SDcpu 2 +SDio 2"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgraphviz-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/emqx-6.3.2-6e4ee3d.tar.gz /tmp/emqx.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY fuzzer/aflnet-mqtt.patch fuzzer/mqtt_aflnet.c fuzzer/parser-test.c fuzzer/aflnet.h fuzzer/alloc-inl.h /tmp/fuzzer/
COPY mqtt_packets.py prepare_seeds.py mqtt.dict /tmp/work/
COPY seeds/ /tmp/work/seeds/

RUN set -eux; \
    echo "${EMQX_ARCHIVE_SHA256}  /tmp/emqx.tar.gz" | sha256sum -c -; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    mkdir -p /src/emqx /opt/aflnet /work/results /work/seeds; \
    tar -xzf /tmp/emqx.tar.gz --strip-components=1 -C /src/emqx; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    cp /tmp/fuzzer/mqtt_aflnet.c /opt/aflnet/mqtt_aflnet.c; \
    git -C /opt/aflnet apply --check /tmp/fuzzer/aflnet-mqtt.patch; \
    git -C /opt/aflnet apply /tmp/fuzzer/aflnet-mqtt.patch; \
    make -C /opt/aflnet -j"${MAKE_JOBS}" afl-fuzz; \
    cp /opt/aflnet/mqtt_aflnet.c /tmp/fuzzer/mqtt_aflnet.c; \
    cc -O2 -Wall -Wextra -Werror -I/tmp/fuzzer /tmp/fuzzer/parser-test.c /tmp/fuzzer/mqtt_aflnet.c -o /tmp/mqtt-parser-test; \
    /tmp/mqtt-parser-test; \
    python3 /tmp/work/prepare_seeds.py /tmp/work/seeds /work/seeds; \
    git -C /src/emqx init; \
    git -C /src/emqx config user.name "Baseline Builder"; \
    git -C /src/emqx config user.email "baseline.invalid@example.invalid"; \
    git -C /src/emqx add -A; \
    git -C /src/emqx commit -m "EMQX 6.3.2 source archive"; \
    git -C /src/emqx tag 6.3.2; \
    PROFILE=emqx-enterprise PKG_VSN=6.3.2 DOWNLOAD_I18N_TRANSLATIONS=false MAKEFLAGS="-j${MAKE_JOBS}" make -C /src/emqx emqx-enterprise-tgz; \
    mkdir -p /opt/emqx-release; \
    cp /src/emqx/_packages/emqx-enterprise/*.tar.gz /opt/emqx-release/emqx-6.3.2.tar.gz; \
    printf 'emqx_source_commit=%s\n' "${EMQX_COMMIT}" > /work/build-lock.txt; \
    printf 'emqx_source_archive_sha256=%s\n' "${EMQX_ARCHIVE_SHA256}" >> /work/build-lock.txt; \
    printf 'aflnet_commit=%s\n' "${AFLNET_COMMIT}" >> /work/build-lock.txt; \
    printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}" >> /work/build-lock.txt; \
    printf 'aflnet_mqtt_patch_sha256=' >> /work/build-lock.txt; sha256sum /tmp/fuzzer/aflnet-mqtt.patch | cut -d ' ' -f1 >> /work/build-lock.txt; \
    printf 'mqtt_parser_sha256=' >> /work/build-lock.txt; sha256sum /tmp/fuzzer/mqtt_aflnet.c | cut -d ' ' -f1 >> /work/build-lock.txt; \
    printf 'builder_image=%s\n' 'ghcr.io/emqx/emqx-builder/6.2-3:1.19.1-28.4.1-7-ubuntu24.04@sha256:7134ef634abc6021f100c2a16cb83b40fed2a44671037ba2d25ca0c0fa21d12d' >> /work/build-lock.txt; \
    printf 'otp=' >> /work/build-lock.txt; erl -noshell -eval 'io:format("~s~n", [erlang:system_info(otp_release)]), halt().' >> /work/build-lock.txt; \
    printf 'elixir=' >> /work/build-lock.txt; elixir --version | sed -n '2p' >> /work/build-lock.txt; \
    printf 'compiler=' >> /work/build-lock.txt; cc --version | sed -n '1p' >> /work/build-lock.txt; \
    printf 'make=' >> /work/build-lock.txt; make --version | sed -n '1p' >> /work/build-lock.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' git make gcc build-essential python3 ca-certificates libgraphviz-dev > /work/container-packages.txt; \
    cp /tmp/work/mqtt_packets.py /tmp/work/prepare_seeds.py /tmp/work/mqtt.dict /work/; \
    mkdir -p /work/fuzzer; \
    cp /tmp/fuzzer/aflnet-mqtt.patch /tmp/fuzzer/mqtt_aflnet.c /tmp/fuzzer/parser-test.c /work/fuzzer/; \
    chmod -R a+rX /work /opt/aflnet /opt/emqx-release; \
    useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin fuzz; \
    chown -R fuzz:fuzz /work /opt/aflnet /opt/emqx-release

COPY fuzzer/broker_lifecycle.c /tmp/fuzzer/broker_lifecycle.c
COPY emqx.conf /work/emqx.conf
COPY service_smoke.py /work/service_smoke.py
COPY wait_mqtt.py /work/wait_mqtt.py
COPY fuzz-driver.sh /work/fuzz-driver.sh
COPY run.sh /work/run.sh
COPY validate.sh /work/validate.sh

RUN chmod +x /work/fuzz-driver.sh /work/run.sh /work/validate.sh \
    && chown -R fuzz:fuzz /work /opt/aflnet /opt/emqx-release \
    && mkdir -p /work/results \
    && chmod 0777 /work/results

RUN set -eu; \
    ELIXIR_VERSION="$(elixir --version 2>&1 | tail -n 1)"; \
    sed -i "s|^elixir=$|elixir=${ELIXIR_VERSION}|" /work/build-lock.txt; \
    mkdir -p /work/dependency-locks; \
    cp /src/emqx/mix.lock /work/dependency-locks/mix.lock; \
    cd /src/emqx; \
    find . -type f -name rebar.lock -exec cp --parents {} /work/dependency-locks/ \;; \
    (cd /work/dependency-locks && find . -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS); \
    chown -R fuzz:fuzz /work/dependency-locks

RUN set -eu; \
    make -C /opt/aflnet -j2 afl-gcc afl-as afl-showmap; \
    AFL_PATH=/opt/aflnet AFL_QUIET=1 /opt/aflnet/afl-gcc /tmp/fuzzer/broker_lifecycle.c -o /work/aflnet-lifecycle; \
    nm /work/aflnet-lifecycle | grep -E '__afl_(area_ptr|manual_init)' >/dev/null; \
    sha256sum /work/aflnet-lifecycle | awk '{print "lifecycle_stub_sha256=" $1}' >> /work/build-lock.txt; \
    chown fuzz:fuzz /work/aflnet-lifecycle /work/build-lock.txt

WORKDIR /work
USER fuzz
ENTRYPOINT ["/bin/bash"]
