ARG DTLS_BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${DTLS_BASE_IMAGE} AS build
ARG WOLFSSL_VERSION=5.9.4
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake bash bison build-essential ca-certificates libgraphviz-dev \
      libtool libtool-bin pkg-config python3 unzip zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
COPY source/ /opt/benchmark/source/
COPY seeds/ /opt/benchmark/seeds/
COPY prepare_seeds.py version-check.c /opt/benchmark/
RUN set -eux; \
    echo '9cd0d69d208d025b16836c177658cc0deebc2a85c4b60898c9bc546bc6cbdf18  /opt/benchmark/source/wolfssl-5.9.4.zip' | sha256sum -c -; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz' | sha256sum -c -; \
    echo '4c1bc55323df91e2cda1e15c1c7e8aa6bb622d3846f1d73f0d760a4a096ec4ac  /opt/benchmark/seeds/gnutls-clienthello-01.raw' | sha256sum -c -; \
    echo '3b2ff59ffc92f6cfd8dbad689d6c10dd530d75e0bea4aa2234185a3753324f6f  /opt/benchmark/seeds/gnutls-clienthello-02.raw' | sha256sum -c -; \
    echo 'f553d5a622082bf7645d74db9c9d812f48e577d79f98c296f1bc91ed8cfd934e  /opt/benchmark/seeds/gnutls-clienthello-03.raw' | sha256sum -c -; \
    unzip -q /opt/benchmark/source/wolfssl-5.9.4.zip -d /tmp; \
    mkdir -p /opt/aflnet /opt/wolfssl/bin /opt/wolfssl/lib /tmp/graphviz-runtime-libs; \
    tar -xzf /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/aflnet.c /opt/aflnet/afl-fuzz.c; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    grep -a -q DTLS12 /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-build-ldd.txt
RUN set -eux; \
    cd /tmp/wolfssl-${WOLFSSL_VERSION}; \
    CC=/opt/aflnet/afl-gcc CFLAGS='-O1 -g -fno-omit-frame-pointer' \
      ./configure --prefix=/opt/wolfssl --enable-dtls; \
    make -j1 examples/server/server; \
    make install; \
    cp examples/server/.libs/server /opt/wolfssl/bin/server; \
    cp -a src/.libs/libwolfssl.so* /opt/wolfssl/lib/; \
    mkdir -p /opt/wolfssl/certs; \
    unzip -p /opt/benchmark/source/wolfssl-${WOLFSSL_VERSION}.zip wolfssl-${WOLFSSL_VERSION}/certs/dh2048.pem \
      > /opt/wolfssl/certs/dh2048.pem; \
    gcc -O2 -I/opt/wolfssl/include /opt/benchmark/version-check.c \
      -L/opt/wolfssl/lib -Wl,-rpath,/opt/wolfssl/lib -lwolfssl \
      -o /opt/wolfssl/bin/version-check; \
    LD_LIBRARY_PATH=/opt/wolfssl/lib /opt/wolfssl/bin/version-check | tee /opt/benchmark/wolfssl-version.txt; \
    grep -Fxq 5.9.4 /opt/benchmark/wolfssl-version.txt; \
    LD_LIBRARY_PATH=/opt/wolfssl/lib ldd /opt/wolfssl/bin/server | tee /opt/benchmark/wolfssl-server-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/wolfssl-server-build-ldd.txt; \
    cp -a /usr/lib/x86_64-linux-gnu/libcgraph.so.6* /usr/lib/x86_64-linux-gnu/libcdt.so.5* \
      /usr/lib/x86_64-linux-gnu/libgvc.so.6* /usr/lib/x86_64-linux-gnu/libpathplan.so.4* \
      /usr/lib/x86_64-linux-gnu/libxdot.so.4* /usr/lib/x86_64-linux-gnu/libltdl.so.7* \
      /tmp/graphviz-runtime-libs/

FROM ${DTLS_BASE_IMAGE} AS runtime
ARG WOLFSSL_VERSION=5.9.4
ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 WOLFSSL_PORT=20220 \
    LD_LIBRARY_PATH=/opt/wolfssl/lib
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash ca-certificates iproute2 openssl python3 zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/benchmark /opt/wolfssl /opt/aflnet /results /run/wolfssl-benchmark \
    && chmod 0777 /results /run/wolfssl-benchmark
COPY --from=build /opt/wolfssl/ /opt/wolfssl/
COPY --from=build /opt/aflnet/ /opt/aflnet/
COPY --from=build /tmp/graphviz-runtime-libs/ /usr/lib/x86_64-linux-gnu/
COPY --from=build /opt/benchmark/afl-fuzz-build-ldd.txt /opt/benchmark/
COPY --from=build /opt/benchmark/wolfssl-version.txt /opt/benchmark/
COPY --from=build /opt/benchmark/wolfssl-server-build-ldd.txt /opt/benchmark/
COPY compose.yaml images.env source-lock.json README.md PACKAGE-MANIFEST.md ACCEPTANCE.md \
     prepare-target.sh prepare_seeds.py protocol_smoke.py replay_queue.py \
     deadline_wrapper.py verify_listener_closed.py run.sh version-check.c /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
RUN set -eux; \
    ldconfig; \
    LD_LIBRARY_PATH=/opt/wolfssl/lib ldd /opt/wolfssl/bin/server | tee /opt/benchmark/wolfssl-server-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/wolfssl-server-runtime-ldd.txt; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    /opt/wolfssl/bin/version-check | tee /opt/benchmark/wolfssl-runtime-version.txt; \
    grep -Fxq "${WOLFSSL_VERSION}" /opt/benchmark/wolfssl-runtime-version.txt; \
    cd /opt/wolfssl; \
    ./bin/server --help > /tmp/server-help.txt 2>&1 || true; \
    cat /tmp/server-help.txt; \
    grep -q -- 'Use UDP DTLS' /tmp/server-help.txt; \
    grep -q -- 'Echo data mode' /tmp/server-help.txt; \
    python3 -m py_compile /opt/benchmark/prepare_seeds.py /opt/benchmark/protocol_smoke.py \
      /opt/benchmark/replay_queue.py /opt/benchmark/deadline_wrapper.py /opt/benchmark/verify_listener_closed.py; \
    python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py
USER root
WORKDIR /opt/wolfssl
ENTRYPOINT []
