ARG BASE_IMAGE=docker.io/library/ubuntu:26.04@sha256:065aa8626841f16057b78b027b464cd59c4fac36c204c72dcbf48d66f5fa8a96
FROM ${BASE_IMAGE} AS build
ENV DEBIAN_FRONTEND=noninteractive \
    AFL_MAP_SIZE=262144 \
    AFLRS_NO_CMPLOG=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake binutils build-essential ca-certificates cmake git \
      libev-dev libgraphviz-dev libnuma-dev libtool make ninja-build patch \
      perl pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/benchmark
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY source/openssl-4.1.0.tar.gz /tmp/openssl.tar.gz
COPY source/nghttp3-v1.19.0.tar.gz /tmp/nghttp3.tar.gz
COPY source/sfparse-4b313cfd2e1b389ae632b36dcd50402307289af2.tar.gz /tmp/sfparse.tar.gz
COPY source/ngtcp2-v1.26.0.tar.gz /tmp/ngtcp2.tar.gz
COPY source/urlparse-c8168839c89fc5c5917c375e1bd6ffeddf3f7f88.tar.gz /tmp/urlparse.tar.gz
COPY source/munit-cb04288a5225645be005a521c537b83c51934ef6.tar.gz /tmp/munit.tar.gz
COPY patches/aflnet-quic.patch /opt/benchmark/aflnet-quic.patch
COPY patches/expand-aflnet-map.py /opt/benchmark/expand-aflnet-map.py
COPY patches/fix-aflnet-toolchain.py /opt/benchmark/fix-aflnet-toolchain.py
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    AFL_PATH=/opt/aflnet \
    CC=/opt/aflnet/afl-gcc \
    CXX=/opt/aflnet/afl-g++
RUN mkdir -p /opt/aflnet /opt/out \
    && tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet \
    && patch --directory=/opt/aflnet --strip=1 --fuzz=0 --input=/opt/benchmark/aflnet-quic.patch \
    && python3 /opt/benchmark/expand-aflnet-map.py /opt/aflnet/config.h \
    && python3 /opt/benchmark/fix-aflnet-toolchain.py /opt/aflnet/Makefile \
    && make -C /opt/aflnet CC=gcc CXX=g++ clean all
RUN mkdir -p /opt/openssl /opt/deps/openssl \
    && tar -xzf /tmp/openssl.tar.gz -C /opt/openssl --strip-components=1 \
    && cd /opt/openssl \
    && ./Configure no-shared no-tests no-asm --prefix=/opt/deps/openssl \
       --openssldir=/opt/deps/openssl/ssl --libdir=lib linux-x86_64 \
    && make -j2 build_all_generated \
    && make -j2 build_sw \
    && make install_sw
RUN mkdir -p /opt/nghttp3/lib/sfparse \
    && tar -xzf /tmp/nghttp3.tar.gz -C /opt/nghttp3 --strip-components=1 \
    && tar -xzf /tmp/sfparse.tar.gz -C /opt/nghttp3/lib/sfparse --strip-components=1 \
    && cmake -S /opt/nghttp3 -B /tmp/nghttp3-build -G Ninja \
       -DCMAKE_BUILD_TYPE=RelWithDebInfo \
       -DCMAKE_C_COMPILER=/opt/aflnet/afl-gcc \
       -DCMAKE_INSTALL_PREFIX=/opt/deps/nghttp3 \
       -DENABLE_LIB_ONLY=ON -DBUILD_TESTING=OFF \
       -DENABLE_STATIC_LIB=ON -DENABLE_SHARED_LIB=OFF \
    && cmake --build /tmp/nghttp3-build -j2 \
    && cmake --install /tmp/nghttp3-build
RUN mkdir -p /opt/ngtcp2/third-party/urlparse /opt/ngtcp2/tests/munit \
    && tar -xzf /tmp/ngtcp2.tar.gz -C /opt/ngtcp2 --strip-components=1 \
    && tar -xzf /tmp/urlparse.tar.gz -C /opt/ngtcp2/third-party/urlparse --strip-components=1 \
    && tar -xzf /tmp/munit.tar.gz -C /opt/ngtcp2/tests/munit --strip-components=1
ENV PKG_CONFIG_PATH=/opt/deps/openssl/lib/pkgconfig:/opt/deps/nghttp3/lib/pkgconfig \
    LD_LIBRARY_PATH=/opt/deps/openssl/lib:/opt/deps/nghttp3/lib
RUN cmake -S /opt/ngtcp2 -B /tmp/ngtcp2-build -G Ninja \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_C_COMPILER=/opt/aflnet/afl-gcc \
      -DCMAKE_CXX_COMPILER=/opt/aflnet/afl-g++ \
      -DCMAKE_INSTALL_PREFIX=/opt/deps/ngtcp2 \
      -DCMAKE_PREFIX_PATH=/opt/deps/nghttp3 \
      -DOPENSSL_ROOT_DIR=/opt/deps/openssl \
      -DENABLE_OPENSSL=ON -DENABLE_SHARED_LIB=ON -DENABLE_STATIC_LIB=OFF \
      -DCMAKE_BUILD_RPATH=/opt/benchmark/lib -DCMAKE_INSTALL_RPATH=/opt/benchmark/lib \
      -DBUILD_TESTING=OFF -DENABLE_WERROR=OFF -DENABLE_ASAN=OFF \
    && cmake --build /tmp/ngtcp2-build --target osslserver -j2 \
    && mkdir -p /opt/out/lib \
    && find /tmp/ngtcp2-build \( -type f -o -type l \) -name 'libngtcp2*.so*' -exec cp -a -t /opt/out/lib '{}' + \
    && find /tmp/ngtcp2-build -type f -name osslserver -executable -exec cp '{}' /opt/out/osslserver ';' \
    && test -x /opt/out/osslserver \
    && OPENSSL_CONF=/dev/null /opt/deps/openssl/bin/openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
       -keyout /opt/out/server.key -out /opt/out/server.crt \
       -subj "/CN=localhost" \
    && chmod 0644 /opt/out/server.key /opt/out/server.crt \
    && { \
         printf '%s\n' 'ngtcp2 v1.26.0 osslserver'; \
         printf '%s\n' 'nghttp3 v1.19.0; OpenSSL 4.1.0'; \
         printf '%s\n' 'target=examples/osslserver; afl=2.56b QUIC datagram patch'; \
         sha256sum /opt/out/osslserver /opt/aflnet/afl-fuzz; \
         LD_LIBRARY_PATH=/opt/out/lib:/opt/deps/openssl/lib:/opt/deps/nghttp3/lib ldd /opt/out/osslserver || true; \
       } > /opt/out/build-info.txt

FROM ${BASE_IMAGE} AS runtime
ENV DEBIAN_FRONTEND=noninteractive \
    AFL_MAP_SIZE=262144 \
    NGTCP2_SERVER=/opt/benchmark/osslserver \
    NGTCP2_KEY=/opt/benchmark/server.key \
    NGTCP2_CERT=/opt/benchmark/server.crt \
    NGTCP2_PORT=4433 \
    AFLNET_BIN=/opt/aflnet/afl-fuzz \
    LD_LIBRARY_PATH=/opt/benchmark/lib
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates libev-dev libgraphviz-dev libnuma-dev procps python3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/out/ /opt/benchmark/
COPY --from=build /opt/aflnet/afl-fuzz /opt/aflnet/afl-fuzz
COPY run.sh build-info.sh deadline_wrapper.py protocol_smoke.py \
     replay_queue.py validate_seeds.py verify_listener_closed.py \
     README.md ACCEPTANCE.md PACKAGE-MANIFEST.md source-lock.json \
     toolchain-lock.json /opt/benchmark/
WORKDIR /opt/benchmark
CMD ["/bin/bash"]
