ARG BASE_IMAGE=ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    ASAN_OPTIONS=detect_leaks=1:abort_on_error=1:symbolize=1
WORKDIR /work

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates clang cmake libclang-rt-18-dev ninja-build perl python3 \
    && rm -rf /var/lib/apt/lists/*

COPY source/boringssl-0.20261105.0.tar.gz source/SHA256SUMS /tmp/source/
COPY PINNED_SOURCE.md README.md run-container.sh summarize.py /work/
COPY source/PROVENANCE.txt /work/build-evidence/source-provenance.txt

RUN chmod 0755 /work/run-container.sh && set -eux; \
    cd /tmp/source; \
    sha256sum -c SHA256SUMS; \
    mkdir -p /src/boringssl /work/results /work/build-evidence; \
    tar -xzf boringssl-0.20261105.0.tar.gz --strip-components=1 -C /src/boringssl; \
    CC=clang CXX=clang++ cmake -S /src/boringssl -B /build/boringssl -G Ninja \
      -DFUZZ=1 -DBUILD_SHARED_LIBS=OFF; \
    cmake --build /build/boringssl --target server --parallel 2; \
    cp -a /src/boringssl/fuzz/server_corpus /work/seeds; \
    { \
      cat /work/PINNED_SOURCE.md; \
      printf '\nsource_archive_sha256=%s\n' '87345c7dc8530f2135bea2e60b11f447474d36668e019b0cef4c57693c063422'; \
      printf 'target=upstream fuzz/server.cc -> fuzz/server\n'; \
      printf 'FUZZ=1 (upstream ASan and edge/indirect-call coverage)\n'; \
      printf 'base_image=%s\n' 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852'; \
      clang --version | head -1; cmake --version | head -1; ninja --version; \
      sha256sum /build/boringssl/fuzz/server; \
    } > /work/build-evidence/build-lock.txt; \
    rm -rf /tmp/source

WORKDIR /work
ENTRYPOINT ["/work/run-container.sh"]
