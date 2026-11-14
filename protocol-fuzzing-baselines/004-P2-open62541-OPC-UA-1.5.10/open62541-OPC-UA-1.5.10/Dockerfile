FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates clang cmake libclang-rt-18-dev make ninja-build patch \
      pkg-config python3 python3-lxml python3-six zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src/open62541
COPY source/open62541-v1.5.10-with-submodules.tar.gz /tmp/open62541-v1.5.10.tar.gz
COPY fuzz_tcp_message.patch /tmp/fuzz_tcp_message.patch
COPY patch-checksums.sha256 /tmp/patch-checksums.sha256

RUN cd /tmp && sha256sum -c patch-checksums.sha256 \
    && tar -xzf /tmp/open62541-v1.5.10.tar.gz --strip-components=1 -C /src/open62541 \
    && cd /src/open62541 \
    && patch --dry-run --fuzz=0 -p1 < /tmp/fuzz_tcp_message.patch \
    && patch --fuzz=0 -p1 < /tmp/fuzz_tcp_message.patch

RUN CC=clang CXX=clang++ cmake -S /src/open62541 -B /src/open62541/build -G Ninja \
      -DCMAKE_BUILD_TYPE=Debug \
      -DUA_BUILD_FUZZING=ON \
      -DUA_BUILD_EXAMPLES=OFF \
      -DUA_BUILD_UNIT_TESTS=OFF \
      -DUA_ENABLE_ENCRYPTION=OFF \
      -DUA_LOGLEVEL=700 \
    && cmake --build /src/open62541/build --target fuzz_tcp_message -j2 \
    && find /src/open62541/build -type f -name fuzz_tcp_message -perm -111 -exec install -D -m 0755 {} /usr/local/bin/fuzz_tcp_message \; \
    && test -x /usr/local/bin/fuzz_tcp_message

WORKDIR /work
ENTRYPOINT ["/usr/local/bin/fuzz_tcp_message"]
