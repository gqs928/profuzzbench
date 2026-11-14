ARG BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${BASE_IMAGE} AS build
ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    AFL_MAP_SIZE=262144 \
    AFLRS_NO_CMPLOG=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      binutils build-essential ca-certificates clang clang-tools curl git \
      lld llvm-dev make openssl patch pkg-config python3 unzip zip \
      libgraphviz-dev libicu-dev libssl-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl --proto '=https' --tlsv1.2 -fsSL \
      https://releases.bazel.build/8.2.1/release/bazel-8.2.1-linux-x86_64 \
      -o /usr/local/bin/bazel \
    && echo '7ff2b6a675b59a791d007c526977d5262ade8fa52efc8e0d1ff9e18859909fc0  /usr/local/bin/bazel' | sha256sum -c - \
    && chmod 0755 /usr/local/bin/bazel
WORKDIR /opt/benchmark
COPY source/ /opt/benchmark/source/
COPY patches/ /opt/benchmark/patches/
RUN mkdir -p /opt/aflnet /opt/quiche /opt/out/certs \
    && tar -xzf /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet \
    && patch --directory=/opt/aflnet --strip=1 --fuzz=0 --input=/opt/benchmark/patches/aflnet-quic.patch \
    && python3 /opt/benchmark/patches/expand-aflnet-map.py /opt/aflnet/config.h \
    && make -C /opt/aflnet clean all \
    && tar -xzf /opt/benchmark/source/google-quiche-23e525e5184bbd98d9722bc3bb3f4ce181efcde4.tar.gz -C /opt/quiche \
    && test "$(cat /opt/quiche/.bazelversion)" = "8.2.1"
ENV PATH=/opt/aflnet:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    CC=/opt/aflnet/afl-gcc \
    CXX=/opt/aflnet/afl-g++
RUN cd /opt/quiche \
    && PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
       CC=/opt/aflnet/afl-gcc CXX=/opt/aflnet/afl-g++ \
       bazel --output_user_root=/tmp/bazel-root build --jobs=1 -c opt \
       --repo_env=CC=/opt/aflnet/afl-gcc \
       --repo_env=CXX=/opt/aflnet/afl-g++ \
       --repo_env=AFL_PATH=/opt/aflnet \
       --action_env=CC=/opt/aflnet/afl-gcc \
       --action_env=CXX=/opt/aflnet/afl-g++ \
       --action_env=AFL_PATH=/opt/aflnet \
       //quiche:quic_server \
    && cp -L /opt/quiche/bazel-bin/quiche/quic_server /opt/out/quic_server \
    && openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
       -keyout /opt/out/certs/server.key -out /opt/out/certs/server.crt \
       -subj "/CN=localhost" \
    && chmod 0644 /opt/out/certs/server.key /opt/out/certs/server.crt \
    && ldd /opt/out/quic_server | tee /opt/out/quic-server-ldd.txt \
    && { \
         echo "Google QUICHE main@23e525e5184bbd98d9722bc3bb3f4ce181efcde4"; \
         echo "target=//quiche:quic_server"; \
         bazel --version; \
         echo "aflnet_commit=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732"; \
         awk '/^#define MAP_SIZE_POW2/ {print "aflnet_map_size=" (2 ^ $3); exit}' /opt/aflnet/config.h; \
         echo "forkserver=matching AFLNet 2.56b vanilla target and fuzzer"; \
         sha256sum /opt/out/quic_server /opt/aflnet/afl-fuzz; \
         cat /opt/out/quic-server-ldd.txt; \
       } > /opt/out/build-info.txt
FROM ${BASE_IMAGE} AS runtime
ENV DEBIAN_FRONTEND=noninteractive \
    AFL_MAP_SIZE=262144 \
    QUICHE_SERVER=/opt/benchmark/quic_server \
    QUICHE_CERT=/opt/benchmark/certs/server.crt \
    QUICHE_KEY=/opt/benchmark/certs/server.key \
    QUICHE_PORT=4433 \
    AFLNET_BIN=/opt/aflnet/afl-fuzz
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates libcgraph6 libgcc-s1 libgvc6 libicu74 libstdc++6 \
      libssl3t64 python3 zlib1g \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/out/ /opt/benchmark/
COPY --from=build /opt/aflnet/afl-fuzz /opt/aflnet/afl-fuzz
COPY run.sh build-info.sh deadline_wrapper.py protocol_smoke.py \
     replay_queue.py validate_seeds.py verify_listener_closed.py \
     README.md ACCEPTANCE.md PACKAGE-MANIFEST.md source-lock.json \
     toolchain-lock.json /opt/benchmark/
WORKDIR /opt/benchmark
CMD ["/bin/bash"]
