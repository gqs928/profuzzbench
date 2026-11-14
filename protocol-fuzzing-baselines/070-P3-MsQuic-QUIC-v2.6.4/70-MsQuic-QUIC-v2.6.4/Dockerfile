ARG BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${BASE_IMAGE} AS build
ENV DEBIAN_FRONTEND=noninteractive \
    AFL_MAP_SIZE=262144 \
    AFLRS_NO_CMPLOG=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      binutils build-essential ca-certificates cmake git libgraphviz-dev libnuma-dev make \
      ninja-build openssl patch perl pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/benchmark
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY source/msquic-v2.6.4.tar.gz /tmp/msquic.tar.gz
COPY patches/aflnet-quic.patch /opt/benchmark/aflnet-quic.patch
COPY patches/expand-aflnet-map.py /opt/benchmark/expand-aflnet-map.py
COPY patches/msquic-quicsample-serve.patch /opt/benchmark/msquic-quicsample-serve.patch
RUN mkdir -p /opt/aflnet /opt/msquic /opt/out/certs \
    && tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet \
    && patch --directory=/opt/aflnet --strip=1 --fuzz=0 --input=/opt/benchmark/aflnet-quic.patch \
    && python3 /opt/benchmark/expand-aflnet-map.py /opt/aflnet/config.h \
    && make -C /opt/aflnet clean all \
    && tar -xzf /tmp/msquic.tar.gz -C /opt/msquic --strip-components=1 \
    && patch --directory=/opt/msquic --strip=1 --fuzz=0 --input=/opt/benchmark/msquic-quicsample-serve.patch \
    && test -f /opt/msquic/submodules/quictls/Configure
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    AFL_PATH=/opt/aflnet \
    CC=/opt/aflnet/afl-gcc \
    CXX=/opt/aflnet/afl-g++
RUN cmake -S /opt/msquic -B /tmp/msquic-build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_COMPILER=/opt/aflnet/afl-gcc \
      -DCMAKE_CXX_COMPILER=/opt/aflnet/afl-g++ \
      -DQUIC_BUILD_TOOLS=ON -DQUIC_BUILD_TEST=OFF -DQUIC_BUILD_PERF=OFF \
      -DQUIC_BUILD_SHARED=OFF -DBUILD_SHARED_LIBS=OFF \
      -DQUIC_TLS_LIB=quictls -DQUIC_USE_SYSTEM_LIBCRYPTO=OFF \
      -DQUIC_ENABLE_LOGGING=OFF -DQUIC_CODE_CHECK=OFF \
      -DQUIC_EMBED_GIT_HASH=OFF \
    && cmake --build /tmp/msquic-build --target quicsample -j2 \
    && find /tmp/msquic-build -type f -name quicsample -executable -exec cp '{}' /opt/out/quicsample ';' \
    && test -x /opt/out/quicsample \
    && openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
       -keyout /opt/out/server.key -out /opt/out/server.crt \
       -subj "/CN=localhost" \
    && chmod 0644 /opt/out/server.key /opt/out/server.crt \
    && { \
         printf '%s\n' 'MsQuic v2.6.4 official release'; \
         printf '%s\n' 'target=src/tools/sample/quicsample'; \
         printf '%s\n' 'sample_patch=keep-server-alive-until-AFLNet-termination'; \
         printf '%s\n' 'tls=quictls bundled pinned submodule'; \
         printf '%s\n' 'aflnet=2.56b QUIC datagram patch; map=262144'; \
         sha256sum /opt/out/quicsample /opt/aflnet/afl-fuzz; \
         ldd /opt/out/quicsample || true; \
       } > /opt/out/build-info.txt

FROM ${BASE_IMAGE} AS runtime
ENV DEBIAN_FRONTEND=noninteractive \
    AFL_MAP_SIZE=262144 \
    MSQUIC_SAMPLE=/opt/benchmark/quicsample \
    MSQUIC_CERT=/opt/benchmark/server.crt \
    MSQUIC_KEY=/opt/benchmark/server.key \
    MSQUIC_PORT=4567 \
    AFLNET_BIN=/opt/aflnet/afl-fuzz
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates libcgraph6 libgvc6 libnuma1 python3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/out/ /opt/benchmark/
COPY --from=build /opt/aflnet/afl-fuzz /opt/aflnet/afl-fuzz
COPY run.sh build-info.sh deadline_wrapper.py protocol_smoke.py \
     replay_queue.py validate_seeds.py verify_listener_closed.py \
     README.md ACCEPTANCE.md PACKAGE-MANIFEST.md source-lock.json \
     toolchain-lock.json /opt/benchmark/
WORKDIR /opt/benchmark
CMD ["/bin/bash"]
