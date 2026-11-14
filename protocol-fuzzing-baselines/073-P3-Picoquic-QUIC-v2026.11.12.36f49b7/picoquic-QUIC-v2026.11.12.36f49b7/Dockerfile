ARG BASE_IMAGE=docker.io/library/ubuntu:26.04@sha256:065aa8626841f16057b78b027b464cd59c4fac36c204c72dcbf48d66f5fa8a96
FROM ${BASE_IMAGE} AS build
ENV DEBIAN_FRONTEND=noninteractive AFL_MAP_SIZE=262144 AFLRS_NO_CMPLOG=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake binutils build-essential ca-certificates cmake git \
      libgraphviz-dev libnuma-dev libssl-dev libtool make openssl patch pkg-config \
      python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/benchmark
COPY source/picoquic-v2026.11.12.36f49b7.tar.gz /tmp/picoquic.tar.gz
COPY source/picotls-e446233b4100ebcdec60901c05bfb7f4cd369c5d.tar.gz /tmp/picotls.tar.gz
COPY source/picotest-a99858e0c33b97b24cd09ceae729f2be33ec01e1.tar.gz /tmp/picotest.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY patches/aflnet-quic.patch /opt/benchmark/aflnet-quic.patch
COPY patches/expand-aflnet-map.py /opt/benchmark/expand-aflnet-map.py
COPY patches/fix-aflnet-toolchain.py /opt/benchmark/fix-aflnet-toolchain.py
RUN echo '15f830e6e00535924b8b2cb5810534fdd57f65d8dacf4c1e1edc795ba88640da  /tmp/picoquic.tar.gz' | sha256sum -c - \
    && echo 'e59194fb970484377ac5c7e39522bbb4103b1e0721d6c409d7b45bb34f8a6f49  /tmp/picotls.tar.gz' | sha256sum -c - \
    && echo 'f3c42d988c8cd1af24dee2e66ce832f3e257bb7766e34167499954c1604c82c0  /tmp/picotest.tar.gz' | sha256sum -c - \
    && echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' | sha256sum -c - \
    && mkdir -p /opt/aflnet /opt/picoquic /opt/picotls/deps/picotest /opt/picoquic-build /opt/out \
    && tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet \
    && patch --directory=/opt/aflnet --strip=1 --fuzz=0 --input=/opt/benchmark/aflnet-quic.patch \
    && python3 /opt/benchmark/expand-aflnet-map.py /opt/aflnet/config.h \
    && python3 /opt/benchmark/fix-aflnet-toolchain.py /opt/aflnet/Makefile \
    && make -C /opt/aflnet CC=gcc CXX=g++ clean all \
    && tar -xzf /tmp/picoquic.tar.gz -C /opt/picoquic --strip-components=1 \
    && tar -xzf /tmp/picotls.tar.gz -C /opt/picotls --strip-components=1 \
    && tar -xzf /tmp/picotest.tar.gz -C /opt/picotls/deps/picotest --strip-components=1 \
    && cd /opt/picotls \
    && CC=/opt/aflnet/afl-gcc CXX=/opt/aflnet/afl-g++ cmake -S . -B . \
       -DCMAKE_BUILD_TYPE=RelWithDebInfo -DWITH_OPENSSL=ON -DWITH_FUSION=OFF \
       -DWITH_BROTLI=OFF -DBUILD_SHARED_LIBS=OFF \
    && cmake --build /opt/picotls -j2 --target picotls-core picotls-minicrypto picotls-openssl \
    && CC=/opt/aflnet/afl-gcc CXX=/opt/aflnet/afl-g++ cmake -S /opt/picoquic -B /opt/picoquic-build \
       -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_DEMO=ON -DBUILD_HTTP=ON \
       -DBUILD_PQBENCH=OFF -DBUILD_LOGLIB=OFF -DBUILD_LOGREADER=OFF \
       -Dpicoquic_BUILD_TESTS=OFF -DBUILD_PICO_SIM=OFF -DWITH_OPENSSL=ON \
       -DPICOQUIC_FETCH_PTLS=OFF -DPTLS_PREFIX=/opt/picotls \
    && cmake --build /opt/picoquic-build -j2 --target picoquicdemo \
    && cp /opt/picoquic-build/picoquicdemo /opt/out/picoquicdemo \
    && OPENSSL_CONF=/dev/null openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
       -keyout /opt/out/server.key -out /opt/out/server.crt -subj "/CN=localhost" \
    && chmod 0644 /opt/out/server.key /opt/out/server.crt \
    && mkdir -p /opt/out/htmlroot \
    && printf '%s\n' 'picoquic QUIC benchmark root' > /opt/out/htmlroot/index.html \
    && { printf '%s\n' 'picoquic v2026.11.12.36f49b7 official picoquicdemo; target source unmodified'; \
         printf '%s\n' 'AFLNet 2.56b; QUIC v1 UDP datagram framing; map=262144'; \
         sha256sum /opt/out/picoquicdemo /opt/aflnet/afl-fuzz /opt/benchmark/fix-aflnet-toolchain.py; \
         ldd /opt/out/picoquicdemo; } > /opt/out/build-info.txt

FROM ${BASE_IMAGE} AS runtime
ENV DEBIAN_FRONTEND=noninteractive AFL_MAP_SIZE=262144 \
    PICOQUIC_SERVER=/opt/benchmark/picoquicdemo \
    PICOQUIC_CERT=/opt/benchmark/server.crt \
    PICOQUIC_KEY=/opt/benchmark/server.key \
    PICOQUIC_HTMLROOT=/opt/benchmark/htmlroot \
    PICOQUIC_PORT=4433 AFLNET_BIN=/opt/aflnet/afl-fuzz
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates libcgraph8 libnuma1 libssl3t64 procps python3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/out/ /opt/benchmark/
COPY --from=build /opt/aflnet/afl-fuzz /opt/aflnet/afl-fuzz
RUN ldd /opt/aflnet/afl-fuzz > /tmp/aflnet.ldd \
    && ldd /opt/benchmark/picoquicdemo > /tmp/target.ldd \
    && ! grep -q 'not found' /tmp/aflnet.ldd /tmp/target.ldd \
    && rm /tmp/aflnet.ldd /tmp/target.ldd
COPY run.sh build-info.sh deadline_wrapper.py protocol_smoke.py replay_queue.py \
     validate_seeds.py verify_listener_closed.py README.md ACCEPTANCE.md \
     PACKAGE-MANIFEST.md source-lock.json toolchain-lock.json /opt/benchmark/
RUN chmod 755 /opt/benchmark/*.sh
WORKDIR /opt/benchmark
CMD ["/bin/bash"]
