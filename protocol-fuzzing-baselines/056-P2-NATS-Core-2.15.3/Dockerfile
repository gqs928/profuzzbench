ARG NATS_IMAGE=docker.io/library/nats:2.15.3@sha256:9d85d87039bfba33baf48de4da32a2ee572bcd6c94f6365d05733a672de49253
ARG DEBIAN_IMAGE=docker.io/library/debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc
ARG AFL_BUILDER_IMAGE=docker.io/rockylinux/rockylinux:9.8@sha256:ed654c694190a670bb5c33f68995b862214fc96ffbdca95e07a8935ba0a3717d

FROM ${NATS_IMAGE} AS official_nats

FROM ${AFL_BUILDER_IMAGE} AS builder
USER root
RUN dnf install -y gcc make patch tar gzip \
    && dnf clean all \
    && rpm -qa | sort > /tmp/rpm-packages-at-build.txt
COPY graphviz-2.44.0-26.el9.x86_64.rpm graphviz-devel-2.44.0-26.el9.x86_64.rpm \
     rocky-linux-9-build-repo.key /tmp/
COPY aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-network-noforkserver.patch aflnet-network-config-terminator.patch \
     aflnet-nats.patch \
     nats_aflnet.inc nats-parser-test.c /nats-adapter/
RUN set -eux; \
    rpm --import /tmp/rocky-linux-9-build-repo.key; \
    echo '31a674d1d3f543f7bd6d6da6694e3d267dbd1b04ca5e739ba0bdab6bc0411d97  /tmp/graphviz-2.44.0-26.el9.x86_64.rpm' | sha256sum -c -; \
    echo '1c48cd518a01e8fda8a20017424b35978de19761ecaf08a74f7a25582904b230  /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm' | sha256sum -c -; \
    rpm --checksig --verbose /tmp/graphviz-2.44.0-26.el9.x86_64.rpm; \
    rpm --checksig --verbose /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm; \
    rpm -Uvh --nodeps /tmp/graphviz-2.44.0-26.el9.x86_64.rpm; \
    rpm -q graphviz | grep -qx 'graphviz-2.44.0-26.el9.x86_64'; \
    rpm -Uvh --nodeps /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm; \
    ldconfig; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' | sha256sum -c -; \
    mkdir -p /opt/aflnet; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /nats-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /nats-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /nats-adapter/aflnet-nats.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /nats-adapter/aflnet-nats.patch; \
    patch --batch --fuzz=0 --dry-run -p1 -d /opt/aflnet -i /nats-adapter/aflnet-network-config-terminator.patch; \
    patch --batch --fuzz=0 --forward -p1 -d /opt/aflnet -i /nats-adapter/aflnet-network-config-terminator.patch; \
    cp /nats-adapter/nats_aflnet.inc /opt/aflnet/nats_aflnet.inc; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    i=0; while [ "$i" -lt 64 ]; do \
      /opt/aflnet/afl-fuzz -N tcp://127.0.0.1/4222 > /tmp/net-config-test.log 2>&1 || true; \
      ! grep -Fq 'Bad syntax used for -N' /tmp/net-config-test.log; \
      grep -Fq 'Required parameters:' /tmp/net-config-test.log; \
      i=$((i + 1)); \
    done; \
    echo 'PASS: AFLNet -N endpoint parser accepted 64 repeated runs'; \
    rm -f /tmp/net-config-test.log; \
    cc -O2 -Wall -Wextra -Werror -I/opt/aflnet /nats-adapter/nats-parser-test.c -o /tmp/nats-parser-test; \
    /tmp/nats-parser-test; \
    grep -a -q NATS /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /tmp/afl-fuzz-build-ldd.txt; \
    if grep -q 'not found' /tmp/afl-fuzz-build-ldd.txt; then exit 1; fi; \
    mkdir -p /tmp/graphviz-runtime-libs; \
    cp -a /usr/lib64/libcgraph.so.6* /usr/lib64/libcdt.so.5* /usr/lib64/libgvc.so.6* \
      /usr/lib64/libpathplan.so.4* /usr/lib64/libxdot.so.4* /usr/lib64/libltdl.so.7* \
      /tmp/graphviz-runtime-libs/; \
    rm -rf /tmp/aflnet.tar.gz /nats-adapter /tmp/nats-parser-test \
      /tmp/graphviz-2.44.0-26.el9.x86_64.rpm /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm \
      /tmp/rocky-linux-9-build-repo.key

ARG DEBIAN_IMAGE
FROM ${DEBIAN_IMAGE} AS runtime
USER root
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 NATS_EXPECTED_VERSION=2.15.3 \
    NATS_HOST=127.0.0.1 NATS_PORT=4222
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash python3 libexpat1 libltdl7 zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/lib/x86_64-linux-gnu
COPY --from=official_nats /nats-server /usr/local/bin/nats-server
COPY --from=builder /opt/aflnet/ /opt/aflnet/
COPY --from=builder /tmp/graphviz-runtime-libs/ /usr/lib/x86_64-linux-gnu/
COPY --from=builder /tmp/rpm-packages-at-build.txt /tmp/rpm-packages-at-build.txt
COPY --from=builder /tmp/afl-fuzz-build-ldd.txt /tmp/afl-fuzz-build-ldd.txt
COPY README.md PACKAGE-MANIFEST.md ACCEPTANCE.md source-lock.json \
     aflnet-nats.patch aflnet-network-config-terminator.patch \
     nats_aflnet.inc nats-parser-test.c nats_client.py \
     prepare_seeds.py protocol_smoke.py replay_queue.py deadline_wrapper.py \
     build.sh run.sh smoke.sh nats.dict images.env compose.yaml seeds-manifest.json /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
RUN set -eux; \
    mkdir -p /opt/benchmark/build-logs; \
    cp /tmp/rpm-packages-at-build.txt /opt/benchmark/build-logs/rpm-packages-at-build.txt; \
    cp /tmp/afl-fuzz-build-ldd.txt /opt/benchmark/build-logs/afl-fuzz-build-ldd.txt; \
    ldconfig; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/build-logs/afl-fuzz-runtime-ldd.txt; \
    if grep -q 'not found' /opt/benchmark/build-logs/afl-fuzz-runtime-ldd.txt; then exit 1; fi; \
    /usr/local/bin/nats-server -v | tee /opt/benchmark/build-logs/nats-server-version.txt; \
    grep -Fq 'v2.15.3' /opt/benchmark/build-logs/nats-server-version.txt; \
    python3 -m py_compile /opt/benchmark/nats_client.py /opt/benchmark/prepare_seeds.py \
      /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py
WORKDIR /opt/benchmark
ENTRYPOINT []
