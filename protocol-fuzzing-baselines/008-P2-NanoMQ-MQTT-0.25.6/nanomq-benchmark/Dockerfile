ARG BUILDER_IMAGE=ghcr.io/emqx/emqx-builder/6.2-3:1.19.1-28.4.1-7-ubuntu24.04@sha256:7134ef634abc6021f100c2a16cb83b40fed2a44671037ba2d25ca0c0fa21d12d
FROM ${BUILDER_IMAGE}

ARG MAKE_JOBS=2
ARG NANOMQ_ARCHIVE_SHA256=1f008a001e024dde3e407435f36dd26dae57c8ecbed415a6d9633d5ecbf1ba04
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG NANOMQ_COMMIT=926179ec41adbb8dbc0a191746ea78d91d53c463

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgraphviz-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/nanomq-0.25.6.tar.gz /tmp/nanomq.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY fuzzer/aflnet-mqtt.patch fuzzer/mqtt_aflnet.c fuzzer/parser-test.c fuzzer/aflnet.h fuzzer/alloc-inl.h /tmp/fuzzer/
COPY mqtt_packets.py prepare_seeds.py mqtt.dict /tmp/work/
COPY seeds/ /tmp/work/seeds/

RUN set -eux; \
    echo "${NANOMQ_ARCHIVE_SHA256}  /tmp/nanomq.tar.gz" | sha256sum -c -; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    mkdir -p /src/nanomq /opt/aflnet /work/results /work/seeds /opt/nanomq; \
    tar -xzf /tmp/nanomq.tar.gz --strip-components=1 -C /src/nanomq; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    cp /tmp/fuzzer/mqtt_aflnet.c /opt/aflnet/mqtt_aflnet.c; \
    git -C /opt/aflnet apply --check /tmp/fuzzer/aflnet-mqtt.patch; \
    git -C /opt/aflnet apply /tmp/fuzzer/aflnet-mqtt.patch; \
    make -C /opt/aflnet -j"${MAKE_JOBS}" afl-fuzz afl-gcc afl-as afl-showmap afl-replay; \
    cc -O2 -Wall -Wextra -Werror -I/tmp/fuzzer /tmp/fuzzer/parser-test.c /tmp/fuzzer/mqtt_aflnet.c -o /tmp/mqtt-parser-test; \
    /tmp/mqtt-parser-test; \
    python3 /tmp/work/prepare_seeds.py /tmp/work/seeds /work/seeds; \
    cmake -S /src/nanomq -B /src/nanomq/build \
      -DCMAKE_C_COMPILER=/opt/aflnet/afl-gcc \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DBUILD_CLIENT=OFF -DBUILD_NANOMQ_CLI=OFF \
      -DNNG_ENABLE_TLS=OFF -DNNG_ENABLE_SQLITE=OFF; \
    cmake --build /src/nanomq/build --parallel "${MAKE_JOBS}"; \
    cp /src/nanomq/build/nanomq/nanomq /opt/nanomq/nanomq; \
    chmod 0755 /opt/nanomq/nanomq; \
    /opt/nanomq/nanomq --help > /work/nanomq-help.txt 2>&1 || true; \
    printf 'nanomq_source_commit=%s\n' "${NANOMQ_COMMIT}" > /work/build-lock.txt; \
    printf 'nanomq_source_archive_sha256=%s\n' "${NANOMQ_ARCHIVE_SHA256}" >> /work/build-lock.txt; \
    printf 'nanomq_nng_submodule_commit=ebd4b8424735f72652b625f9167663683164aafd\n' >> /work/build-lock.txt; \
    printf 'nanomq_l8w8jwt_submodule_commit=ee445f6ea334aac03daa9cbc1efea630f7744aba\n' >> /work/build-lock.txt; \
    printf 'nanomq_nftp_codec_submodule_commit=e14f1811b21cc0301f758e3317c730f96e96a604\n' >> /work/build-lock.txt; \
    printf 'aflnet_commit=%s\n' "${AFLNET_COMMIT}" >> /work/build-lock.txt; \
    printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}" >> /work/build-lock.txt; \
    printf 'aflnet_mqtt_patch_sha256=' >> /work/build-lock.txt; sha256sum /tmp/fuzzer/aflnet-mqtt.patch | cut -d ' ' -f1 >> /work/build-lock.txt; \
    printf 'mqtt_parser_sha256=' >> /work/build-lock.txt; sha256sum /tmp/fuzzer/mqtt_aflnet.c | cut -d ' ' -f1 >> /work/build-lock.txt; \
    printf 'nanomq_binary_sha256=' >> /work/build-lock.txt; sha256sum /opt/nanomq/nanomq | cut -d ' ' -f1 >> /work/build-lock.txt; \
    printf 'builder_image=%s\n' 'ghcr.io/emqx/emqx-builder/6.2-3:1.19.1-28.4.1-7-ubuntu24.04@sha256:7134ef634abc6021f100c2a16cb83b40fed2a44671037ba2d25ca0c0fa21d12d' >> /work/build-lock.txt; \
    printf 'compiler=' >> /work/build-lock.txt; cc --version | sed -n '1p' >> /work/build-lock.txt; \
    printf 'cmake=' >> /work/build-lock.txt; cmake --version | sed -n '1p' >> /work/build-lock.txt; \
    printf 'make=' >> /work/build-lock.txt; make --version | sed -n '1p' >> /work/build-lock.txt; \
    printf 'cmake_flags=-DCMAKE_C_COMPILER=/opt/aflnet/afl-gcc -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_CLIENT=OFF -DBUILD_NANOMQ_CLI=OFF -DNNG_ENABLE_TLS=OFF -DNNG_ENABLE_SQLITE=OFF\n' >> /work/build-lock.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' git make gcc build-essential cmake python3 ca-certificates libgraphviz-dev > /work/container-packages.txt; \
    mkdir -p /work/fuzzer; \
    cp /tmp/fuzzer/aflnet-mqtt.patch /tmp/fuzzer/mqtt_aflnet.c /tmp/fuzzer/parser-test.c /work/fuzzer/; \
    cp /tmp/work/mqtt_packets.py /tmp/work/prepare_seeds.py /tmp/work/mqtt.dict /work/; \
    chmod -R a+rX /work /opt/aflnet /opt/nanomq; \
    useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin fuzz; \
    chown -R fuzz:fuzz /work /opt/aflnet /opt/nanomq

COPY nanomq.conf /work/nanomq.conf
COPY service_smoke.py /work/service_smoke.py
COPY wait_mqtt.py /work/wait_mqtt.py
COPY target-start.sh /work/target-start.sh
COPY run.sh /work/run.sh
COPY validate.sh /work/validate.sh

RUN chmod +x /work/target-start.sh /work/run.sh /work/validate.sh \
    && chown -R fuzz:fuzz /work \
    && chmod 0777 /work/results

WORKDIR /work
USER fuzz
ENTRYPOINT ["/bin/bash"]
