ARG BASE_IMAGE=docker.io/library/ubuntu:26.04@sha256:065aa8626841f16057b78b027b464cd59c4fac36c204c72dcbf48d66f5fa8a96
FROM ${BASE_IMAGE} AS build
ENV DEBIAN_FRONTEND=noninteractive AFL_MAP_SIZE=262144 AFLRS_NO_CMPLOG=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake binutils build-essential ca-certificates git libgraphviz-dev \
      libnuma-dev libtool make patch perl pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/benchmark
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY source/openssl-4.1.0.tar.gz /tmp/openssl.tar.gz
COPY patches/aflnet-quic.patch /opt/benchmark/aflnet-quic.patch
COPY patches/expand-aflnet-map.py /opt/benchmark/expand-aflnet-map.py
COPY patches/fix-aflnet-toolchain.py /opt/benchmark/fix-aflnet-toolchain.py
ENV AFL_PATH=/opt/aflnet CC=/opt/aflnet/afl-gcc CXX=/opt/aflnet/afl-g++
RUN mkdir -p /opt/aflnet /opt/openssl /opt/deps/openssl /opt/out \
    && tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet \
    && patch --directory=/opt/aflnet --strip=1 --fuzz=0 --input=/opt/benchmark/aflnet-quic.patch \
    && python3 /opt/benchmark/expand-aflnet-map.py /opt/aflnet/config.h \
    && python3 /opt/benchmark/fix-aflnet-toolchain.py /opt/aflnet/Makefile \
    && make -C /opt/aflnet CC=gcc CXX=g++ clean all \
    && tar -xzf /tmp/openssl.tar.gz -C /opt/openssl --strip-components=1 \
    && cd /opt/openssl \
    && ./Configure no-shared no-asm no-tests enable-quic --prefix=/opt/deps/openssl \
       --openssldir=/opt/deps/openssl/ssl --libdir=lib linux-x86_64 \
    && make -j2 build_all_generated \
    && make -j2 build_sw \
    && make install_sw \
    && /opt/aflnet/afl-gcc -O1 -g -Wall -Wsign-compare \
       -I/opt/deps/openssl/include \
       -o /opt/out/openssl-quic-server \
       /opt/openssl/demos/quic/server/server.c \
       -Wl,--start-group /opt/deps/openssl/lib/libssl.a /opt/deps/openssl/lib/libcrypto.a \
       -Wl,--end-group -pthread -ldl -lz \
    && OPENSSL_CONF=/dev/null /opt/deps/openssl/bin/openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
       -keyout /opt/out/server.key -out /opt/out/server.crt -subj "/CN=localhost" \
    && chmod 0644 /opt/out/server.key /opt/out/server.crt \
    && { printf '%s\n' 'OpenSSL QUIC server 4.1.0; demo source unmodified'; \
         printf '%s\n' 'AFLNet 2.56b; QUIC v1 UDP datagram framing; map=262144'; \
         sha256sum /opt/out/openssl-quic-server /opt/aflnet/afl-fuzz /opt/benchmark/fix-aflnet-toolchain.py; \
         ldd /opt/out/openssl-quic-server || true; } > /opt/out/build-info.txt

FROM ${BASE_IMAGE} AS runtime
ENV DEBIAN_FRONTEND=noninteractive AFL_MAP_SIZE=262144 \
    OPENSSL_QUIC_SERVER=/opt/benchmark/openssl-quic-server \
    OPENSSL_QUIC_CERT=/opt/benchmark/server.crt \
    OPENSSL_QUIC_KEY=/opt/benchmark/server.key \
    OPENSSL_QUIC_PORT=4433 AFLNET_BIN=/opt/aflnet/afl-fuzz
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates libcgraph8 libnuma1 procps python3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/out/ /opt/benchmark/
COPY --from=build /opt/aflnet/afl-fuzz /opt/aflnet/afl-fuzz
RUN ldd /opt/aflnet/afl-fuzz > /tmp/aflnet.ldd \
    && ldd /opt/benchmark/openssl-quic-server > /tmp/target.ldd \
    && ! grep -q 'not found' /tmp/aflnet.ldd /tmp/target.ldd \
    && rm /tmp/aflnet.ldd /tmp/target.ldd
COPY run.sh build-info.sh deadline_wrapper.py protocol_smoke.py replay_queue.py \
     validate_seeds.py verify_listener_closed.py README.md ACCEPTANCE.md \
     PACKAGE-MANIFEST.md source-lock.json toolchain-lock.json /opt/benchmark/
WORKDIR /opt/benchmark
CMD ["/bin/bash"]
