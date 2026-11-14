ARG BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${BASE_IMAGE} AS build
ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    AFL_MAP_SIZE=262144 \
    AFL_PATH=/opt/aflnet
RUN apt-get update && apt-get install -y --no-install-recommends \
      binutils build-essential ca-certificates cmake curl \
      git golang-go libevent-dev libgraphviz-dev libssl-dev ninja-build \
      openssl perl pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/benchmark
COPY source/ /opt/benchmark/source/
COPY patches/ /opt/benchmark/patches/
RUN mkdir -p /opt/aflnet /opt/lsquic /opt/boringssl \
      /opt/lsquic/src/liblsquic/ls-qpack /opt/lsquic/src/lshpack \
      /opt/out/certs /opt/out/www \
    && tar -xzf source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet \
    && patch --directory=/opt/aflnet --strip=1 --fuzz=0 --input=/opt/benchmark/patches/aflnet-quic.patch \
    && python3 /opt/benchmark/patches/expand-aflnet-map.py /opt/aflnet/config.h \
    && make -C /opt/aflnet clean all \
    && tar -xzf source/lsquic-v4.11.1.tar.gz -C /opt/lsquic --strip-components=1 \
    && tar -xzf source/ls-qpack-91567706c41c0d97ab8dc576873ecd472d7869fa.tar.gz \
       -C /opt/lsquic/src/liblsquic/ls-qpack --strip-components=1 \
    && tar -xzf source/ls-hpack-cf0f70dd10b352194c97448eb5d00b4aa484f531.tar.gz \
       -C /opt/lsquic/src/lshpack --strip-components=1 \
    && tar -xzf source/boringssl-10c780b1a3f67f9b8269502833808942979d5004.tar.gz \
       -C /opt/boringssl

RUN cd /opt/boringssl \
    && PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
       CC=/opt/aflnet/afl-gcc CXX=/opt/aflnet/afl-g++ \
       AFL_PATH=/opt/aflnet cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF . \
    && make -j2 crypto ssl \
    && test -s /opt/boringssl/libcrypto.a \
    && test -s /opt/boringssl/libssl.a

RUN PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
      CC=/opt/aflnet/afl-gcc CXX=/opt/aflnet/afl-g++ \
      AFL_PATH=/opt/aflnet cmake -S /opt/lsquic -B /opt/lsquic/build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_COMPILER=/opt/aflnet/afl-gcc \
      -DCMAKE_CXX_COMPILER=/opt/aflnet/afl-g++ \
      -DLSQUIC_LIBSSL=BORINGSSL -DLIBSSL_DIR=/opt/boringssl \
      -DLSQUIC_BIN=ON -DLSQUIC_TESTS=OFF -DLSQUIC_DEVEL=OFF \
    && cmake --build /opt/lsquic/build --target http_server --parallel 2 \
    && cp -L /opt/lsquic/build/bin/http_server /opt/out/http_server \
    && openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
       -keyout /opt/out/certs/server.key -out /opt/out/certs/server.crt \
       -subj "/CN=quic.tech" \
    && printf 'LSQUIC v4.11.1 fuzz target\n' > /opt/out/www/index.html \
    && chmod 0644 /opt/out/certs/server.key /opt/out/certs/server.crt \
    && ldd /opt/out/http_server | tee /opt/out/http-server-ldd.txt \
    && { \
         echo "LSQUIC v4.11.1 (tag commit 2f4cd42f27cf8e9b0a0f43e376a618ec8ce4a7ff)"; \
         echo "BoringSSL main@10c780b1a3f67f9b8269502833808942979d5004"; \
         echo "CMake $(cmake --version | head -1)"; \
         echo "Go $(go version)"; \
         echo "compiler=$(gcc --version | head -1); aflnet_wrappers=afl-gcc,afl-g++"; \
         echo "aflnet_commit=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732"; \
         awk '/^#define MAP_SIZE_POW2/ {print "aflnet_map_size=" (2 ^ $3); exit}' /opt/aflnet/config.h; \
         sha256sum /opt/out/http_server /opt/aflnet/afl-fuzz; \
         cat /opt/out/http-server-ldd.txt; \
       } > /opt/out/build-info.txt

FROM ${BASE_IMAGE} AS runtime
ENV DEBIAN_FRONTEND=noninteractive \
    AFL_MAP_SIZE=262144 \
    LSQUIC_SERVER=/opt/benchmark/http_server \
    LSQUIC_CERT=/opt/benchmark/certs/server.crt \
    LSQUIC_KEY=/opt/benchmark/certs/server.key \
    LSQUIC_ROOT=/opt/benchmark/www \
    LSQUIC_PORT=4433 \
    AFLNET_BIN=/opt/aflnet/afl-fuzz
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates libevent-2.1-7t64 libcgraph6 libgcc-s1 libgvc6 \
      libstdc++6 python3 zlib1g \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/out/ /opt/benchmark/
COPY --from=build /opt/aflnet/afl-fuzz /opt/aflnet/afl-fuzz
COPY run.sh build-info.sh deadline_wrapper.py protocol_smoke.py \
     replay_queue.py validate_seeds.py verify_listener_closed.py \
     README.md ACCEPTANCE.md PACKAGE-MANIFEST.md source-lock.json \
     toolchain-lock.json /opt/benchmark/
WORKDIR /opt/benchmark
CMD ["/bin/bash"]
