ARG BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    RUSTUP_HOME=/root/.rustup \
    CARGO_HOME=/root/.cargo \
    PATH=/root/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    AFL_MAP_SIZE=262144 \
    AFLRS_NO_CMPLOG=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential ca-certificates clang cmake curl git libclang-dev libgraphviz-dev \
      libssl-dev libunwind-dev llvm make ninja-build patch perl pkg-config \
      python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
      | sh -s -- -y --profile minimal --default-toolchain 1.100.0 \
    && rustup component add rustfmt

RUN cargo install cargo-afl --version 0.18.2 --locked \
    && cargo afl config --build --force

WORKDIR /opt/benchmark
COPY source/ /opt/benchmark/source/
COPY patches/ /opt/benchmark/patches/

RUN mkdir -p /opt/aflnet /opt/quiche \
    && tar -xzf /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet \
    && patch --directory=/opt/aflnet --strip=1 --fuzz=0 --input=/opt/benchmark/patches/aflnet-quic.patch \
    && python3 /opt/benchmark/patches/expand-aflnet-map.py /opt/aflnet/config.h \
    && make -C /opt/aflnet clean all \
    && tar -xzf /opt/benchmark/source/quiche-0.30.0.tar.gz -C /opt/quiche --strip-components=1 \
    && patch --directory=/opt/quiche --strip=1 --fuzz=0 --input=/opt/benchmark/patches/quiche-add-seedgen.patch \
    && cd /opt/quiche \
    && AFLRS_NO_CMPLOG=1 cargo afl build --release --package quiche_apps --features fuzzing --bins \
    && mkdir -p /opt/benchmark/seeds /opt/benchmark/www \
    && /opt/quiche/target/release/quiche-seedgen /opt/benchmark/seeds/quic-v1-client-initial.bin \
    && printf 'Cloudflare quiche 0.30.0\n' > /opt/benchmark/www/index.html \
    && chmod -R a+rX /opt/benchmark/seeds /opt/benchmark/www

# Keep runtime scripts in a later layer so protocol-specific harness repairs do
# not invalidate the expensive Rust/BoringSSL instrumented build above.
COPY . /opt/benchmark

ENV AFLNET_BIN=/opt/aflnet/afl-fuzz \
    AFL_OLD_FORKSERVER=1 \
    QUICHE_SERVER=/opt/quiche/target/release/quiche-server \
    QUICHE_CERT=/opt/quiche/apps/src/bin/cert.crt \
    QUICHE_KEY=/opt/quiche/apps/src/bin/cert.key \
    QUICHE_ROOT=/opt/benchmark/www

WORKDIR /opt/benchmark
CMD ["/bin/bash"]
