ARG PDNS_BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
ARG AFL_BUILDER_IMAGE=docker.io/rockylinux/rockylinux:9.8@sha256:ed654c694190a670bb5c33f68995b862214fc96ffbdca95e07a8935ba0a3717d
ARG PDNS_PACKAGE_VERSION=5.4.9-1pdns.ubuntu24.04

FROM ${AFL_BUILDER_IMAGE} AS afl_builder
USER root
RUN dnf install -y gcc make patch tar gzip \
    && dnf clean all
COPY graphviz-2.44.0-26.el9.x86_64.rpm graphviz-devel-2.44.0-26.el9.x86_64.rpm \
     rocky-linux-9-build-repo.key /tmp/
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY source/aflnet-network-noforkserver.patch source/aflnet-network-config-terminator.patch \
     source/aflnet-dns-tcp.patch \
     source/dns-tcp-aflnet.inc source/dns-tcp-parser-test.c /tmp/dns-adapter/
RUN set -eux; \
    rpm --import /tmp/rocky-linux-9-build-repo.key; \
    echo '31a674d1d3f543f7bd6d6da6694e3d267dbd1b04ca5e739ba0bdab6bc0411d97  /tmp/graphviz-2.44.0-26.el9.x86_64.rpm' | sha256sum -c -; \
    echo '1c48cd518a01e8fda8a20017424b35978de19761ecaf08a74f7a25582904b230  /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm' | sha256sum -c -; \
    rpm --checksig --verbose /tmp/graphviz-2.44.0-26.el9.x86_64.rpm; \
    rpm --checksig --verbose /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm; \
    rpm -Uvh --nodeps /tmp/graphviz-2.44.0-26.el9.x86_64.rpm; \
    rpm -Uvh --nodeps /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm; \
    ldconfig; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' | sha256sum -c -; \
    mkdir -p /opt/aflnet; tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/dns-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/dns-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --fuzz=0 --dry-run -p1 -d /opt/aflnet -i /tmp/dns-adapter/aflnet-network-config-terminator.patch; \
    patch --batch --fuzz=0 --forward -p1 -d /opt/aflnet -i /tmp/dns-adapter/aflnet-network-config-terminator.patch; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/dns-adapter/aflnet-dns-tcp.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/dns-adapter/aflnet-dns-tcp.patch; \
    cp /tmp/dns-adapter/dns-tcp-aflnet.inc /opt/aflnet/dns_tcp_aflnet.inc; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    i=0; while [ "$i" -lt 64 ]; do \
      /opt/aflnet/afl-fuzz -N tcp://127.0.0.1/5300 > /tmp/net-config-test.log 2>&1 || true; \
      ! grep -Fq 'Bad syntax used for -N' /tmp/net-config-test.log; \
      grep -Fq 'Required parameters:' /tmp/net-config-test.log; \
      i=$((i + 1)); \
    done; \
    echo 'PASS: AFLNet -N DNS/TCP endpoint parser accepted 64 repeated runs'; \
    rm -f /tmp/net-config-test.log; \
    cc -std=c99 -O2 -Wall -Wextra -Werror /tmp/dns-adapter/dns-tcp-parser-test.c -o /tmp/dns-tcp-parser-test; \
    /tmp/dns-tcp-parser-test; \
    grep -a -q DNS_TCP /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /tmp/afl-fuzz-build-ldd.txt; \
    if grep -q 'not found' /tmp/afl-fuzz-build-ldd.txt; then exit 1; fi; \
    mkdir -p /tmp/graphviz-runtime-libs; \
    cp -a /usr/lib64/libcgraph.so.6* /usr/lib64/libcdt.so.5* /usr/lib64/libgvc.so.6* \
      /usr/lib64/libpathplan.so.4* /usr/lib64/libxdot.so.4* /usr/lib64/libltdl.so.7* \
      /tmp/graphviz-runtime-libs/; \
    rm -rf /tmp/aflnet.tar.gz /tmp/dns-adapter /tmp/net-config-test.log /tmp/graphviz-2.44.0-26.el9.x86_64.rpm \
      /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm /tmp/rocky-linux-9-build-repo.key

FROM ${PDNS_BASE_IMAGE} AS runtime
ARG PDNS_PACKAGE_VERSION
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 PDNS_PORT=5300
USER root
RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get install -y --no-install-recommends bash ca-certificates curl gnupg python3 libgvc6; \
    install -d -m 0755 /etc/apt/keyrings /etc/apt/preferences.d; \
    curl -fsSL https://repo.powerdns.com/FD380FBB-pub.asc -o /etc/apt/keyrings/pdns-rec-54-pub.asc; \
    fingerprint=$(gpg --show-keys --with-colons /etc/apt/keyrings/pdns-rec-54-pub.asc | awk -F: '$1 == "fpr" {print $10; exit}'); \
    test "$fingerprint" = '9FAAA5577E8FCF62093D036C1B0C6205FD380FBB'; \
    printf 'deb [arch=amd64 signed-by=/etc/apt/keyrings/pdns-rec-54-pub.asc] https://repo.powerdns.com/ubuntu noble-rec-54 main\n' > /etc/apt/sources.list.d/pdns.list; \
    printf 'Package: pdns-recursor\nPin: version %s\nPin-Priority: 1001\n' "$PDNS_PACKAGE_VERSION" > /etc/apt/preferences.d/pdns-rec-54; \
    printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d; chmod 0755 /usr/sbin/policy-rc.d; \
    apt-get update; \
    apt-get install -y --no-install-recommends "pdns-recursor=$PDNS_PACKAGE_VERSION"; \
    rm -f /usr/sbin/policy-rc.d; \
    test "$(dpkg-query -W -f='${Version}' pdns-recursor)" = "$PDNS_PACKAGE_VERSION"; \
    mkdir -p /opt/benchmark /run/pdns-benchmark; \
    chown pdns:pdns /run/pdns-benchmark; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*
COPY --from=afl_builder /opt/aflnet/ /opt/aflnet/
COPY --from=afl_builder /tmp/graphviz-runtime-libs/ /usr/lib/x86_64-linux-gnu/
COPY README.md PACKAGE-MANIFEST.md ACCEPTANCE.md source-lock.json \
     source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
     source/aflnet-network-noforkserver.patch source/aflnet-network-config-terminator.patch \
     source/aflnet-dns-tcp.patch \
     source/dns-tcp-aflnet.inc source/dns-tcp-parser-test.c \
     prepare_seeds.py protocol_smoke.py recursor_probe.py replay_queue.py \
     verify_listener_closed.py deadline_wrapper.py start-pdns.sh stop-pdns.sh reset-pdns.sh \
     run.sh post-smoke.sh \
     dns-tcp.dict recursor.yml fuzz.test.zone seeds-manifest.json /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
RUN set -eux; \
    ldconfig; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    if grep -q 'not found' /opt/benchmark/afl-fuzz-runtime-ldd.txt; then exit 1; fi; \
    pdns_recursor --version | tee /opt/benchmark/pdns-version.txt; \
    grep -Fq '5.4.9' /opt/benchmark/pdns-version.txt; \
    test "$(dpkg-query -W -f='${Version}' pdns-recursor)" = '5.4.9-1pdns.ubuntu24.04'; \
    python3 -m py_compile /opt/benchmark/prepare_seeds.py /opt/benchmark/protocol_smoke.py \
      /opt/benchmark/recursor_probe.py /opt/benchmark/replay_queue.py /opt/benchmark/deadline_wrapper.py; \
    pdns_recursor --config-dir=/opt/benchmark --config=check; \
    grep -a -q DNS_TCP /opt/aflnet/afl-fuzz; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py
WORKDIR /opt/benchmark
ENTRYPOINT []
