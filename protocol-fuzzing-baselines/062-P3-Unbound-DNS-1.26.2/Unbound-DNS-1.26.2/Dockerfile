ARG UNBOUND_BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

FROM ${UNBOUND_BASE_IMAGE} AS build
ARG UNBOUND_VERSION=1.26.2
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake bash build-essential ca-certificates gnupg libevent-dev \
      libexpat1-dev libssl-dev pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
COPY source/ /opt/benchmark/source/
RUN set -eux; \
    echo 'd8ee7aa6bbb3ff1be7d9e57637d0d0ec2f18273a8efff1a0afe2c665858b96f7  /opt/benchmark/source/unbound-1.26.2.tar.gz' | sha256sum -c -; \
    gpgv --keyring /opt/benchmark/source/nlnetlabs.certs \
      /opt/benchmark/source/unbound-1.26.2.tar.gz.asc \
      /opt/benchmark/source/unbound-1.26.2.tar.gz; \
    mkdir -p /tmp/unbound-src /opt/unbound; \
    tar -xzf /opt/benchmark/source/unbound-${UNBOUND_VERSION}.tar.gz -C /tmp/unbound-src; \
    cd /tmp/unbound-src/unbound-${UNBOUND_VERSION}; \
    ./configure --prefix=/opt/unbound --with-ssl --with-libevent --disable-shared; \
    make -j2; make install; \
    /opt/unbound/sbin/unbound -V | tee /opt/benchmark/unbound-build-version.txt; \
    grep -Fq "Version ${UNBOUND_VERSION}" /opt/benchmark/unbound-build-version.txt
RUN apt-get update && apt-get install -y --no-install-recommends graphviz-dev \
    && mkdir -p /tmp/graphviz-runtime-libs \
    && cp -a /usr/lib/x86_64-linux-gnu/libcgraph.so.6* \
      /usr/lib/x86_64-linux-gnu/libcdt.so.5* /usr/lib/x86_64-linux-gnu/libgvc.so.6* \
      /usr/lib/x86_64-linux-gnu/libpathplan.so.4* /usr/lib/x86_64-linux-gnu/libxdot.so.4* \
      /usr/lib/x86_64-linux-gnu/libltdl.so.7* /tmp/graphviz-runtime-libs/ \
    && rm -rf /var/lib/apt/lists/*
RUN set -eux; \
    mkdir -p /opt/aflnet; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz' | sha256sum -c -; \
    tar -xzf /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/aflnet.c /opt/aflnet/afl-fuzz.c; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /opt/benchmark/source/aflnet-network-noforkserver.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /opt/benchmark/source/aflnet-network-noforkserver.patch; \
    patch --batch --fuzz=0 --dry-run -p1 -d /opt/aflnet -i /opt/benchmark/source/aflnet-network-config-terminator.patch; \
    patch --batch --fuzz=0 --forward -p1 -d /opt/aflnet -i /opt/benchmark/source/aflnet-network-config-terminator.patch; \
    patch --batch --fuzz=0 --dry-run -p1 -d /opt/aflnet -i /opt/benchmark/source/aflnet-dns-tcp.patch; \
    patch --batch --fuzz=0 --forward -p1 -d /opt/aflnet -i /opt/benchmark/source/aflnet-dns-tcp.patch; \
    cp /opt/benchmark/source/dns-tcp-aflnet.inc /opt/aflnet/dns_tcp_aflnet.inc; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    i=0; while [ "$i" -lt 64 ]; do \
      /opt/aflnet/afl-fuzz -N tcp://127.0.0.1/5300 > /tmp/net-config-test.log 2>&1 || true; \
      ! grep -Fq 'Bad syntax used for -N' /tmp/net-config-test.log; \
      grep -Fq 'Required parameters:' /tmp/net-config-test.log; \
      i=$((i + 1)); \
    done; \
    echo 'PASS: AFLNet -N DNS/TCP endpoint parser accepted 64 repeated runs'; \
    /usr/bin/cc -B/usr/bin/ -std=c99 -O2 -Wall -Wextra -Werror \
      /opt/benchmark/source/dns-tcp-parser-test.c -o /tmp/dns-tcp-parser-test; \
    /tmp/dns-tcp-parser-test; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-build-ldd.txt

FROM ${UNBOUND_BASE_IMAGE} AS runtime
ARG UNBOUND_VERSION=1.26.2
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 UNBOUND_PORT=5300
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash ca-certificates libevent-2.1-7t64 libexpat1 libssl3 python3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin unbound \
    && mkdir -p /opt/benchmark /run/unbound-benchmark
COPY --from=build /opt/unbound/ /opt/unbound/
COPY --from=build /opt/aflnet/ /opt/aflnet/
COPY --from=build /tmp/graphviz-runtime-libs/ /usr/lib/x86_64-linux-gnu/
COPY --from=build /opt/benchmark/unbound-build-version.txt /opt/benchmark/
COPY --from=build /opt/benchmark/afl-fuzz-build-ldd.txt /opt/benchmark/
COPY source/ /opt/benchmark/source/
COPY unbound.conf fuzz.test.zone dns-tcp.dict prepare_seeds.py protocol_smoke.py \
     unbound_probe.py replay_queue.py verify_listener_closed.py deadline_wrapper.py \
     start-unbound.sh stop-unbound.sh reset-unbound.sh run.sh README.md \
     PACKAGE-MANIFEST.md ACCEPTANCE.md source-lock.json /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
RUN set -eux; \
    mkdir -p /results; \
    ldconfig; \
    ldd /opt/unbound/sbin/unbound | tee /opt/benchmark/unbound-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/unbound-runtime-ldd.txt; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    /opt/unbound/sbin/unbound -V | tee /opt/benchmark/unbound-version.txt; \
    grep -Fq "Version ${UNBOUND_VERSION}" /opt/benchmark/unbound-version.txt; \
    /opt/unbound/sbin/unbound-checkconf /opt/benchmark/unbound.conf; \
    python3 -m py_compile /opt/benchmark/prepare_seeds.py /opt/benchmark/protocol_smoke.py \
      /opt/benchmark/unbound_probe.py /opt/benchmark/replay_queue.py /opt/benchmark/deadline_wrapper.py; \
    grep -a -q DNS_TCP /opt/aflnet/afl-fuzz; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py
WORKDIR /opt/benchmark
ENTRYPOINT []
