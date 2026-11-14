ARG KNOT_BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${KNOT_BASE_IMAGE}

ARG DEBIAN_FRONTEND=noninteractive
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 \
    PATH=/opt/knot/sbin:/opt/knot/bin:/opt/aflnet:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake bash build-essential ca-certificates gnupg graphviz-dev \
      libedit-dev libgnutls28-dev libidn2-dev liblmdb-dev liburcu-dev libtool \
      pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/ /opt/benchmark/source/
COPY source-lock.json /opt/benchmark/source-lock.json
RUN set -eux; \
    echo '2916ac117ac77d1f2341a6562e47d797493521b791b414960a382cb5bc113e21  /opt/benchmark/source/knot-3.6.2.tar.xz' | sha256sum -c -; \
    mkdir -m 700 /tmp/knot-release-keyring; \
    gpg --homedir /tmp/knot-release-keyring --import /opt/benchmark/source/knot-keyblock.asc; \
    gpg --homedir /tmp/knot-release-keyring --fingerprint --with-colons | grep -Fq '742FA4E95829B6C5EAC6B85710BB7AF6FEBBD6AB'; \
    gpg --homedir /tmp/knot-release-keyring --verify /opt/benchmark/source/knot-3.6.2.tar.xz.asc /opt/benchmark/source/knot-3.6.2.tar.xz; \
    tar -xJf /opt/benchmark/source/knot-3.6.2.tar.xz -C /tmp; \
    cd /tmp/knot-3.6.2; autoreconf -if; \
    ./configure --prefix=/opt/knot --sysconfdir=/opt/knot/etc \
      --localstatedir=/var/lib/knot --with-storage=/tmp/knot-storage \
      --with-rundir=/tmp/knot-rundir --disable-documentation --disable-static \
      --disable-fastparser --enable-quic=no; \
    make -j2; make install; \
    /opt/knot/sbin/knotd -V | tee /opt/benchmark/knotd-version.txt; \
    grep -Fq '3.6.2' /opt/benchmark/knotd-version.txt; \
    mkdir -p /opt/aflnet; tar -xzf /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
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
    rm -f /tmp/net-config-test.log; \
    /usr/bin/cc -B/usr/bin/ -std=c99 -O2 -Wall -Wextra -Werror -I/opt/benchmark/source \
      /opt/benchmark/source/dns-tcp-parser-test.c -o /tmp/dns-tcp-parser-test; \
    /tmp/dns-tcp-parser-test; grep -a -q DNS_TCP /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-build-ldd.txt; \
    rm -f /tmp/net-config-test.log; \
    useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin knot; \
    mkdir -p /opt/benchmark/zones /tmp/knot-rundir /tmp/knot-storage; \
    chmod 1777 /tmp/knot-rundir /tmp/knot-storage; \
    cp /opt/knot/etc/knot.sample.conf /opt/benchmark/knot-sample.conf 2>/dev/null || true; \
    ldconfig

COPY knot.conf fuzz.test.zone dns-tcp.dict prepare_seeds.py knot_probe.py \
     protocol_smoke.py replay_queue.py deadline_wrapper.py start-knot.sh \
     stop-knot.sh reset-knot.sh run.sh README.md PACKAGE-MANIFEST.md ACCEPTANCE.md \
     source-lock.json /opt/benchmark/
RUN set -eux; \
    cp /opt/benchmark/fuzz.test.zone /opt/benchmark/zones/fuzz.test.zone; \
    python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds; \
    python3 -m py_compile /opt/benchmark/prepare_seeds.py /opt/benchmark/knot_probe.py \
      /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py \
      /opt/benchmark/deadline_wrapper.py; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py; \
    chown -R knot:knot /opt/benchmark/zones /tmp/knot-rundir /tmp/knot-storage

WORKDIR /opt/benchmark
ENTRYPOINT []
