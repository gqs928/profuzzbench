ARG ZOOKEEPER_IMAGE=docker.io/library/zookeeper:3.9.7@sha256:3b91be30a1e7294956efab116f2189b87ec586b356e81ad4ea6452742323ecb8
ARG AFL_BUILDER_IMAGE=docker.io/rockylinux/rockylinux:9.8@sha256:ed654c694190a670bb5c33f68995b862214fc96ffbdca95e07a8935ba0a3717d

FROM ${AFL_BUILDER_IMAGE} AS builder
USER root
RUN dnf install -y gcc make patch tar gzip \
    && dnf clean all \
    && rpm -qa | sort > /tmp/rpm-packages-at-build.txt

COPY graphviz-2.44.0-26.el9.x86_64.rpm graphviz-devel-2.44.0-26.el9.x86_64.rpm \
     rocky-linux-9-build-repo.key /tmp/
COPY aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-network-noforkserver.patch aflnet-zookeeper.patch \
     zookeeper_aflnet.inc zookeeper-parser-test.c \
     /zookeeper-adapter/
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
    patch --batch --dry-run -p1 -d /opt/aflnet -i /zookeeper-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /zookeeper-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /zookeeper-adapter/aflnet-zookeeper.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /zookeeper-adapter/aflnet-zookeeper.patch; \
    cp /zookeeper-adapter/zookeeper_aflnet.inc /opt/aflnet/zookeeper_aflnet.inc; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    cc -O2 -Wall -Wextra -Werror -I/opt/aflnet /zookeeper-adapter/zookeeper-parser-test.c -o /tmp/zookeeper-parser-test; \
    /tmp/zookeeper-parser-test; \
    grep -a -q ZOOKEEPER /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /tmp/afl-fuzz-build-ldd.txt; \
    if grep -q 'not found' /tmp/afl-fuzz-build-ldd.txt; then exit 1; fi; \
    mkdir -p /tmp/graphviz-runtime-libs; \
    cp -a /usr/lib64/libcgraph.so.6* /usr/lib64/libcdt.so.5* /usr/lib64/libgvc.so.6* \
      /usr/lib64/libpathplan.so.4* /usr/lib64/libxdot.so.4* /usr/lib64/libltdl.so.7* \
      /tmp/graphviz-runtime-libs/; \
    rm -rf /tmp/aflnet.tar.gz /zookeeper-adapter /tmp/zookeeper-parser-test \
      /tmp/graphviz-2.44.0-26.el9.x86_64.rpm /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm \
      /tmp/rocky-linux-9-build-repo.key

ARG ZOOKEEPER_IMAGE
FROM ${ZOOKEEPER_IMAGE} AS runtime
USER root
ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    ZK_EXPECTED_VERSION=3.9.7 \
    ZK_PORT=2181 \
    ZOO_CONF_DIR=/opt/benchmark/conf \
    ZOOCFGDIR=/opt/benchmark/conf \
    ZOO_DATA_DIR=/tmp/zookeeper-native-bench-data \
    ZOO_DATA_LOG_DIR=/tmp/zookeeper-native-bench-datalog \
    ZOO_LOG_DIR=/results/zookeeper-logs
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 libexpat1 libltdl7 zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/lib/x86_64-linux-gnu
COPY --from=builder /opt/aflnet/ /opt/aflnet/
COPY --from=builder /tmp/graphviz-runtime-libs/ /usr/lib/x86_64-linux-gnu/
COPY --from=builder /tmp/rpm-packages-at-build.txt /tmp/rpm-packages-at-build.txt
COPY --from=builder /tmp/afl-fuzz-build-ldd.txt /tmp/afl-fuzz-build-ldd.txt
COPY . /opt/benchmark/
RUN set -eux; \
    mkdir -p /opt/benchmark/build-logs; \
    cp /tmp/rpm-packages-at-build.txt /opt/benchmark/build-logs/rpm-packages-at-build.txt; \
    cp /tmp/afl-fuzz-build-ldd.txt /opt/benchmark/build-logs/afl-fuzz-build-ldd.txt; \
    ldconfig; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/build-logs/afl-fuzz-runtime-ldd.txt; \
    if grep -q 'not found' /opt/benchmark/build-logs/afl-fuzz-runtime-ldd.txt; then exit 1; fi; \
    chmod +x /opt/benchmark/*.sh
WORKDIR /opt/benchmark
ENTRYPOINT []
