ARG DTLS_BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${DTLS_BASE_IMAGE} AS build
ARG GNUTLS_VERSION=3.8.13
ENV DEBIAN_FRONTEND=noninteractive LD_LIBRARY_PATH=/opt/gnutls/lib
RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake bash bison build-essential ca-certificates clang gettext \
      gperf graphviz-dev libbrotli-dev libidn2-dev libp11-kit-dev libtasn1-6-dev \
      libtool libunistring-dev nettle-dev openssl pkg-config python3 xz-utils \
      zlib1g-dev gnupg \
    && rm -rf /var/lib/apt/lists/*
ARG NETTLE_VERSION=3.10.2
ENV LD_LIBRARY_PATH=/opt/nettle/lib:/opt/gnutls/lib
COPY source/ /opt/benchmark/source/
COPY seeds/ /opt/benchmark/seeds/
COPY prepare_seeds.py /opt/benchmark/prepare_seeds.py
COPY capture_seeds.py /opt/benchmark/capture_seeds.py
RUN set -eux; \
    echo 'fe9ff51cb1f2abb5e65a6b8c10a92da0ab5ab6eaf26e7fc2b675c45f1fb519b5  /opt/benchmark/source/nettle-3.10.2.tar.gz' | sha256sum -c -; \
    echo '9cc1319ede378148f4c729ad889e3c0bd461d974ea590916f3480b93257a1d0b  /opt/benchmark/source/nettle-3.10.2.tar.gz.sig' | sha256sum -c -; \
    echo '1235812a12ce07515303f9ebb138225e4021342832c1465040fee2e849524888  /opt/benchmark/source/nettle-distribution-key.gpg' | sha256sum -c -; \
    gpgv --keyring /opt/benchmark/source/nettle-distribution-key.gpg \
      /opt/benchmark/source/nettle-3.10.2.tar.gz.sig /opt/benchmark/source/nettle-3.10.2.tar.gz; \
    echo 'ffed8ec1bf09c2426d4f14aae377de4753b53e537d685e604e99a8b16ca9c97e  /opt/benchmark/source/gnutls-3.8.13.tar.xz' | sha256sum -c -; \
    echo 'a47ae67e65375cedf0e0af830db4f29b29365283c1c3661a47d3d67601b9eada  /opt/benchmark/source/gnutls-release-keyring.gpg' | sha256sum -c -; \
    echo 'c28f45567e618aaedeff8b0e1570e7dc78064f97806de94ee67554bc579f1046  /opt/benchmark/source/gnutls-release-signers.gpg' | sha256sum -c -; \
    gpgv --keyring /opt/benchmark/source/gnutls-release-signers.gpg \
      /opt/benchmark/source/gnutls-3.8.13.tar.xz.sig /opt/benchmark/source/gnutls-3.8.13.tar.xz; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz' | sha256sum -c -; \
    echo '4c1bc55323df91e2cda1e15c1c7e8aa6bb622d3846f1d73f0d760a4a096ec4ac  /opt/benchmark/seeds/gnutls-clienthello-01.raw' | sha256sum -c -; \
    echo '3b2ff59ffc92f6cfd8dbad689d6c10dd530d75e0bea4aa2234185a3753324f6f  /opt/benchmark/seeds/gnutls-clienthello-02.raw' | sha256sum -c -; \
    echo 'f553d5a622082bf7645d74db9c9d812f48e577d79f98c296f1bc91ed8cfd934e  /opt/benchmark/seeds/gnutls-clienthello-03.raw' | sha256sum -c -; \
    /usr/bin/python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds; \
    mkdir -p /opt/aflnet /opt/nettle /opt/gnutls /tmp/nettle-src /tmp/gnutls-src; \
    tar -xzf /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    tar -xzf /opt/benchmark/source/nettle-${NETTLE_VERSION}.tar.gz -C /tmp/nettle-src; \
    tar -xJf /opt/benchmark/source/gnutls-${GNUTLS_VERSION}.tar.xz -C /tmp/gnutls-src
RUN set -eux; \
    cd /tmp/nettle-src/nettle-${NETTLE_VERSION}; \
    ./configure --prefix=/opt/nettle --libdir=/opt/nettle/lib; \
    make -j1; \
    make install; \
    PKG_CONFIG_PATH=/opt/nettle/lib/pkgconfig pkg-config --modversion nettle | grep -Fx "${NETTLE_VERSION}"; \
    ldd /opt/nettle/lib/libnettle.so | tee /opt/benchmark/nettle-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/nettle-build-ldd.txt
RUN set -eux; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/aflnet.c /opt/aflnet/afl-fuzz.c; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    grep -a -q DTLS12 /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-build-ldd.txt
RUN set -eux; \
    cd /tmp/gnutls-src/gnutls-${GNUTLS_VERSION}; \
    PKG_CONFIG_PATH=/opt/nettle/lib/pkgconfig \
      CPPFLAGS='-I/opt/nettle/include' LDFLAGS='-L/opt/nettle/lib' \
      LD_LIBRARY_PATH=/opt/nettle/lib:/opt/gnutls/lib \
      CC=/opt/aflnet/afl-gcc \
      CFLAGS='-O1 -g -fno-omit-frame-pointer' \
      ./configure --prefix=/opt/gnutls --disable-doc --disable-guile --disable-tests; \
    make -j1; \
    make install; \
    /opt/gnutls/bin/gnutls-serv --version | tee /opt/benchmark/gnutls-serv-build-version.txt; \
    grep -Fq 'gnutls-serv 3.8.13' /opt/benchmark/gnutls-serv-build-version.txt; \
    /opt/gnutls/bin/gnutls-cli --version | tee /opt/benchmark/gnutls-cli-build-version.txt; \
    grep -Fq 'gnutls-cli 3.8.13' /opt/benchmark/gnutls-cli-build-version.txt; \
    ldd /opt/gnutls/bin/gnutls-serv | tee /opt/benchmark/gnutls-serv-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/gnutls-serv-build-ldd.txt
RUN mkdir -p /tmp/graphviz-runtime-libs \
    && cp -a /usr/lib/x86_64-linux-gnu/libcgraph.so.6* \
      /usr/lib/x86_64-linux-gnu/libcdt.so.5* /usr/lib/x86_64-linux-gnu/libgvc.so.6* \
      /usr/lib/x86_64-linux-gnu/libpathplan.so.4* /usr/lib/x86_64-linux-gnu/libxdot.so.4* \
      /usr/lib/x86_64-linux-gnu/libltdl.so.7* /tmp/graphviz-runtime-libs/

FROM ${DTLS_BASE_IMAGE} AS runtime
ARG GNUTLS_VERSION=3.8.13
ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 GNUTLS_PORT=20220 \
    LD_LIBRARY_PATH=/opt/gnutls/lib
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash ca-certificates iproute2 libbrotli1 libidn2-0 libp11-kit0 \
      libtasn1-6 libunistring5 libnettle8t64 libhogweed6t64 openssl python3 zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/benchmark /results /run/gnutls-benchmark \
    && chmod 0777 /results /run/gnutls-benchmark
COPY --from=build /opt/gnutls/ /opt/gnutls/
COPY --from=build /opt/nettle/ /opt/nettle/
COPY --from=build /opt/aflnet/ /opt/aflnet/
COPY --from=build /tmp/graphviz-runtime-libs/ /usr/lib/x86_64-linux-gnu/
COPY --from=build /opt/benchmark/source/ /opt/benchmark/source/
COPY --from=build /opt/benchmark/gnutls-serv-build-version.txt /opt/benchmark/
COPY --from=build /opt/benchmark/gnutls-cli-build-version.txt /opt/benchmark/
COPY --from=build /opt/benchmark/gnutls-serv-build-ldd.txt /opt/benchmark/
COPY --from=build /opt/benchmark/afl-fuzz-build-ldd.txt /opt/benchmark/
COPY --from=build /opt/benchmark/seeds-manifest.json /opt/benchmark/
COPY compose.yaml images.env source-lock.json README.md PACKAGE-MANIFEST.md ACCEPTANCE.md \
     prepare_seeds.py capture_seeds.py protocol_smoke.py replay_queue.py deadline_wrapper.py \
     verify_listener_closed.py prepare-target.sh run.sh /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
ENV LD_LIBRARY_PATH=/opt/nettle/lib:/opt/gnutls/lib
RUN set -eux; \
    ldconfig; \
    ldd /opt/gnutls/bin/gnutls-serv | tee /opt/benchmark/gnutls-serv-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/gnutls-serv-runtime-ldd.txt; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    /opt/gnutls/bin/gnutls-serv --version | tee /opt/benchmark/gnutls-serv-version.txt; \
    grep -Fq "gnutls-serv ${GNUTLS_VERSION}" /opt/benchmark/gnutls-serv-version.txt; \
    /opt/gnutls/bin/gnutls-serv --help | grep -q -- '--udp'; \
    /opt/gnutls/bin/gnutls-serv --help | grep -q -- '--nocookie'; \
    /opt/gnutls/bin/gnutls-cli --help | grep -q -- '--udp'; \
    /opt/gnutls/bin/gnutls-cli --help | grep -q -- '--insecure'; \
    python3 -m py_compile /opt/benchmark/prepare_seeds.py /opt/benchmark/capture_seeds.py \
      /opt/benchmark/protocol_smoke.py \
      /opt/benchmark/replay_queue.py /opt/benchmark/deadline_wrapper.py; \
    python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py
USER root
WORKDIR /opt/benchmark
ENTRYPOINT []
