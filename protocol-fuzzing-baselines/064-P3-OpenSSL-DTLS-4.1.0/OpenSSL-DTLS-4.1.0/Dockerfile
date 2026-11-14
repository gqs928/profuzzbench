ARG DTLS_BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

FROM ${DTLS_BASE_IMAGE} AS build
ARG OPENSSL_VERSION=4.1.0
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash build-essential ca-certificates perl python3 zlib1g-dev gnupg xz-utils \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends libgraphviz-dev \
    && rm -rf /var/lib/apt/lists/*
COPY source/ /opt/benchmark/source/
COPY seeds/ /opt/benchmark/seeds/
COPY prepare_seeds.py /opt/benchmark/prepare_seeds.py
RUN set -eux; \
    echo '50c17baf54cb008f6ce42d50deb4b28050a1aad711636cabd4b241c7e90cc2fd  /opt/benchmark/source/openssl-4.1.0.tar.gz' | sha256sum -c -; \
    echo 'd66bbf4cb7810c1c3dcab2aa29b824c9f3793cd28288e7aa698ef848c0e6db33  /opt/benchmark/source/openssl-4.1.0.tar.gz.asc' | sha256sum -c -; \
    echo '56e106cd1c44bdb117aec24795f6dfbecaa9bfa0a2901b85331f0059aad16d53  /opt/benchmark/source/openssl-release-pubkeys.asc' | sha256sum -c -; \
    echo '09686dd513f68d78fd6a19148b8b63de7d950f0f148a2092f65dce623a1099a3  /opt/benchmark/source/openssl-release-pubkeys.gpg' | sha256sum -c -; \
    gpgv --keyring /opt/benchmark/source/openssl-release-pubkeys.gpg \
      /opt/benchmark/source/openssl-4.1.0.tar.gz.asc /opt/benchmark/source/openssl-4.1.0.tar.gz; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz' | sha256sum -c -; \
    mkdir -p /opt/aflnet /opt/openssl /tmp/openssl-src; \
    tar -xzf /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    tar -xzf /opt/benchmark/source/openssl-${OPENSSL_VERSION}.tar.gz -C /tmp/openssl-src; \
    /usr/bin/python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds
RUN set -eux; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/aflnet.c /opt/aflnet/afl-fuzz.c; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    grep -a -q DTLS12 /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-build-ldd.txt
RUN set -eux; \
    cd /tmp/openssl-src/openssl-${OPENSSL_VERSION}; \
    CC=/opt/aflnet/afl-gcc CFLAGS='-O1 -g -fno-omit-frame-pointer' \
      ./Configure linux-x86_64 --prefix=/opt/openssl --libdir=lib \
        --openssldir=/opt/openssl/ssl no-tests no-docs; \
    make -j1 build_sw; \
    make install_sw; \
    LD_LIBRARY_PATH=/opt/openssl/lib /opt/openssl/bin/openssl version -a | tee /opt/benchmark/openssl-build-version.txt; \
    grep -Fq 'OpenSSL 4.1.0 ' /opt/benchmark/openssl-build-version.txt; \
    LD_LIBRARY_PATH=/opt/openssl/lib /opt/openssl/bin/openssl s_server -help > /tmp/s_server-help.txt 2>&1 || true; \
    grep -q -- '-dtls1_2' /tmp/s_server-help.txt; \
    LD_LIBRARY_PATH=/opt/openssl/lib ldd /opt/openssl/bin/openssl | tee /opt/benchmark/openssl-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/openssl-build-ldd.txt
COPY dtls_echo_server.c /opt/benchmark/dtls_echo_server.c
RUN set -eux; \
    /opt/aflnet/afl-gcc -O1 -g -fno-omit-frame-pointer \
      -I/opt/openssl/include -o /opt/openssl/bin/dtls_echo_server \
      /opt/benchmark/dtls_echo_server.c -L/opt/openssl/lib \
      -Wl,-rpath,/opt/openssl/lib -lssl -lcrypto -pthread; \
    ldd /opt/openssl/bin/dtls_echo_server | tee /opt/benchmark/dtls-echo-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/dtls-echo-build-ldd.txt
RUN mkdir -p /tmp/graphviz-runtime-libs \
    && cp -a /usr/lib/x86_64-linux-gnu/libcgraph.so.6* \
      /usr/lib/x86_64-linux-gnu/libcdt.so.5* /usr/lib/x86_64-linux-gnu/libgvc.so.6* \
      /usr/lib/x86_64-linux-gnu/libpathplan.so.4* /usr/lib/x86_64-linux-gnu/libxdot.so.4* \
      /usr/lib/x86_64-linux-gnu/libltdl.so.7* /tmp/graphviz-runtime-libs/

FROM ${DTLS_BASE_IMAGE} AS runtime
ARG OPENSSL_VERSION=4.1.0
ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 OPENSSL_PORT=20220 \
    LD_LIBRARY_PATH=/opt/openssl/lib OPENSSL_CONF=/dev/null
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash ca-certificates iproute2 python3 zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/benchmark /results /run/openssl-dtls-benchmark \
    && chmod 0777 /results /run/openssl-dtls-benchmark
COPY --from=build /opt/openssl/ /opt/openssl/
COPY --from=build /opt/aflnet/ /opt/aflnet/
COPY --from=build /tmp/graphviz-runtime-libs/ /usr/lib/x86_64-linux-gnu/
COPY --from=build /opt/benchmark/source/ /opt/benchmark/source/
COPY --from=build /opt/benchmark/openssl-build-version.txt /opt/benchmark/
COPY --from=build /opt/benchmark/openssl-build-ldd.txt /opt/benchmark/
COPY --from=build /opt/benchmark/afl-fuzz-build-ldd.txt /opt/benchmark/
COPY --from=build /opt/benchmark/seeds-manifest.json /opt/benchmark/
COPY Dockerfile compose.yaml images.env source-lock.json README.md PACKAGE-MANIFEST.md ACCEPTANCE.md \
     prepare_seeds.py prepare-target.sh protocol_smoke.py capture_seeds.py \
     replay_queue.py deadline_wrapper.py verify_listener_closed.py run.sh /opt/benchmark/
COPY dtls_echo_server.c /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
RUN set -eux; \
    ldconfig; \
    ldd /opt/openssl/bin/openssl | tee /opt/benchmark/openssl-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/openssl-runtime-ldd.txt; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    ldd /opt/openssl/bin/dtls_echo_server | tee /opt/benchmark/dtls-echo-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/dtls-echo-runtime-ldd.txt; \
    /opt/openssl/bin/openssl version | tee /opt/benchmark/openssl-runtime-version.txt; \
    grep -Fq "OpenSSL ${OPENSSL_VERSION} " /opt/benchmark/openssl-runtime-version.txt; \
    /opt/openssl/bin/openssl list -providers | grep -q default; \
    python3 -m py_compile /opt/benchmark/prepare_seeds.py /opt/benchmark/capture_seeds.py \
      /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py \
      /opt/benchmark/deadline_wrapper.py; \
    python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py
USER root
WORKDIR /opt/benchmark
ENTRYPOINT []
