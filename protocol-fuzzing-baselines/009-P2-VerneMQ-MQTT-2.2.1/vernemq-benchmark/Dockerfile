ARG BUILDER_IMAGE=ghcr.io/emqx/emqx-builder/6.2-3:1.19.1-28.4.1-7-ubuntu24.04@sha256:7134ef634abc6021f100c2a16cb83b40fed2a44671037ba2d25ca0c0fa21d12d
FROM ${BUILDER_IMAGE}

ARG MAKE_JOBS=2
ARG VERNE_VERSION=2.2.1
ARG VERNE_COMMIT=29bf9605aefb5969f08ab03f701626148904a61b
ARG VERNE_ARCHIVE_SHA256=57a99d45b0116fedb1b3d3499ff3b23a2a54431573e03e1bf6a1b0d1e9b69b0f
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    ERL_FLAGS="+S 4:4 +SDcpu 2 +SDio 2"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git libsnappy-dev libgraphviz-dev python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global http.version HTTP/1.1

COPY source/vernemq-2.2.1.tar.gz /tmp/vernemq.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY fuzzer/ /tmp/fuzzer/
COPY seeds/ /tmp/seeds/
COPY mqtt_packets.py prepare_seeds.py mqtt.dict wait_mqtt.py service_smoke.py /tmp/work/
COPY vernemq.conf vmq.acl /tmp/work/
COPY run.sh validate.sh /tmp/work/

RUN set -eux; \
    echo "${VERNE_ARCHIVE_SHA256}  /tmp/vernemq.tar.gz" | sha256sum -c -; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    mkdir -p /src/vernemq /opt/aflnet /opt/vernemq /work/results /work/seeds /work/fuzzer; \
    tar -xzf /tmp/vernemq.tar.gz --strip-components=1 -C /src/vernemq; \
    git -C /src/vernemq init -q; \
    git -C /src/vernemq config user.name 'Baseline Builder'; \
    git -C /src/vernemq config user.email 'baseline.invalid@example.invalid'; \
    git -C /src/vernemq add -A; \
    git -C /src/vernemq -c user.name='Baseline Builder' -c user.email='baseline.invalid@example.invalid' commit -qm 'VerneMQ 2.2.1 source archive'; \
    git -C /src/vernemq tag 2.2.1; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    cp /tmp/fuzzer/mqtt_aflnet.c /opt/aflnet/mqtt_aflnet.c; \
    git -C /opt/aflnet apply --check /tmp/fuzzer/aflnet-mqtt.patch; \
    git -C /opt/aflnet apply /tmp/fuzzer/aflnet-mqtt.patch; \
    make -C /opt/aflnet -j"${MAKE_JOBS}" afl-fuzz afl-gcc afl-showmap; \
    cc -O2 -Wall -Wextra -Werror -I/tmp/fuzzer /tmp/fuzzer/parser-test.c /tmp/fuzzer/mqtt_aflnet.c -o /tmp/mqtt-parser-test; \
    /tmp/mqtt-parser-test; \
    make -C /src/vernemq -j"${MAKE_JOBS}" GIT_VERSION="${VERNE_VERSION}" rel; \
    cp -a /src/vernemq/_build/default/rel/vernemq/. /opt/vernemq/; \
    cp /tmp/work/vernemq.conf /opt/vernemq/etc/vernemq.conf; \
    cp /tmp/work/vmq.acl /opt/vernemq/etc/vmq.acl; \
    chmod +x /opt/vernemq/bin/vernemq /opt/vernemq/bin/vmq-admin /opt/vernemq/bin/vmq-passwd; \
    cp /tmp/work/vernemq.conf /work/vernemq.conf; \
    cp /tmp/work/mqtt_packets.py /tmp/work/prepare_seeds.py /tmp/work/mqtt.dict /tmp/work/wait_mqtt.py /tmp/work/service_smoke.py /work/; \
    cp /tmp/work/run.sh /tmp/work/validate.sh /work/; \
    cp /tmp/fuzzer/* /work/fuzzer/; \
    cp -a /tmp/seeds/. /work/seeds/; \
    printf 'vernemq_version=%s\n' "${VERNE_VERSION}" > /work/build-lock.txt; \
    printf 'vernemq_source_commit=%s\n' "${VERNE_COMMIT}" >> /work/build-lock.txt; \
    printf 'vernemq_source_archive_sha256=%s\n' "${VERNE_ARCHIVE_SHA256}" >> /work/build-lock.txt; \
    printf 'snapshot_git_commit=' >> /work/build-lock.txt; git -C /src/vernemq rev-parse HEAD >> /work/build-lock.txt; \
    printf 'aflnet_commit=%s\n' "${AFLNET_COMMIT}" >> /work/build-lock.txt; \
    printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}" >> /work/build-lock.txt; \
    printf 'aflnet_mqtt_patch_sha256=' >> /work/build-lock.txt; sha256sum /tmp/fuzzer/aflnet-mqtt.patch | cut -d ' ' -f1 >> /work/build-lock.txt; \
    printf 'mqtt_adapter_sha256=' >> /work/build-lock.txt; sha256sum /tmp/fuzzer/mqtt_aflnet.c | cut -d ' ' -f1 >> /work/build-lock.txt; \
    printf 'builder_image=%s\n' 'ghcr.io/emqx/emqx-builder/6.2-3:1.19.1-28.4.1-7-ubuntu24.04@sha256:7134ef634abc6021f100c2a16cb83b40fed2a44671037ba2d25ca0c0fa21d12d' >> /work/build-lock.txt; \
    printf 'otp=' >> /work/build-lock.txt; erl -noshell -eval 'io:format("~s~n", [erlang:system_info(otp_release)]), halt().' >> /work/build-lock.txt; \
    printf 'compiler=' >> /work/build-lock.txt; cc --version | sed -n '1p' >> /work/build-lock.txt; \
    printf 'make=' >> /work/build-lock.txt; make --version | sed -n '1p' >> /work/build-lock.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' git make gcc build-essential python3 ca-certificates libsnappy-dev libgraphviz-dev > /work/container-packages.txt

RUN set -eux; \
    cd /opt/vernemq; ./bin/vernemq version > /work/vernemq-version.txt 2>&1 || { cat /work/vernemq-version.txt; exit 1; }; \
    make -C /opt/aflnet -j"${MAKE_JOBS}" afl-as; \
    AFL_PATH=/opt/aflnet AFL_QUIET=1 /opt/aflnet/afl-gcc /tmp/fuzzer/broker_lifecycle.c -o /work/aflnet-lifecycle; \
    nm /work/aflnet-lifecycle | grep -E '__afl_(area_ptr|manual_init)' >/dev/null; \
    printf 'lifecycle_stub_sha256=' >> /work/build-lock.txt; sha256sum /work/aflnet-lifecycle | cut -d ' ' -f1 >> /work/build-lock.txt; \
    printf 'lifecycle_stub_instrumentation_symbols=' >> /work/build-lock.txt; nm /work/aflnet-lifecycle | grep -c __afl_area_ptr >> /work/build-lock.txt; \
    chmod +x /work/run.sh /work/validate.sh; \
    useradd --system --uid 10001 --create-home --home-dir /home/fuzz --shell /usr/sbin/nologin fuzz; \
    chown -R fuzz:fuzz /work /opt/vernemq /opt/aflnet; \
    chmod -R a+rX /work /opt/vernemq /opt/aflnet

WORKDIR /work
USER fuzz
ENTRYPOINT ["/bin/bash"]
