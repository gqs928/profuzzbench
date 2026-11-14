ARG BASE_IMAGE=ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    ASAN_OPTIONS=detect_leaks=1:abort_on_error=1:symbolize=1 \
    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
WORKDIR /work

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates clang cmake gnupg libclang-rt-18-dev libcmocka-dev libssl-dev ninja-build \
    pkg-config python3 xz-utils zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/ /tmp/source/
COPY run-container.sh summarize.py README.md /work/

RUN chmod 0755 /work/run-container.sh && set -eux; \
    cd /tmp/source; \
    sha256sum -c SHA256SUMS; \
    mkdir -m 700 /tmp/libssh-gnupg; \
    gpg --homedir /tmp/libssh-gnupg --batch --no-autostart --import libssh-0.12.2-signing-key.asc; \
    actual_fingerprint=$(gpg --homedir /tmp/libssh-gnupg --batch --no-autostart --with-colons --fingerprint | awk -F: '$1 == "fpr" { print $10; exit }'); \
    test "$actual_fingerprint" = '88A228D89B07C2C77D0C780903D5DF8CFDD3E8E7'; \
    gpg --homedir /tmp/libssh-gnupg --batch --no-autostart --verify libssh-0.12.2.tar.xz.asc libssh-0.12.2.tar.xz > /work/source-signature-verification.txt 2>&1; \
    cat /work/source-signature-verification.txt; \
    mkdir -p /src/libssh /work/results /work/build-evidence; \
    tar -xJf libssh-0.12.2.tar.xz --strip-components=1 -C /src/libssh; \
    CC=clang CXX=clang++ cmake -S /src/libssh -B /build/libssh -G Ninja \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
      '-DCMAKE_C_FLAGS_RELWITHDEBINFO=-O1 -g -fno-omit-frame-pointer -fsanitize=fuzzer-no-link,address,undefined' \
      '-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O1 -g -fno-omit-frame-pointer -fsanitize=fuzzer-no-link,address,undefined' \
      -DCMAKE_EXE_LINKER_FLAGS='-fsanitize=address,undefined' \
      -DBUILD_SHARED_LIBS=ON -DBUILD_STATIC_LIB=ON \
      -DUNIT_TESTING=ON -DFUZZ_TESTING=ON \
      -DWITH_SERVER=ON -DWITH_EXEC=OFF -DWITH_GSSAPI=OFF \
      -DWITH_INSECURE_NONE=ON \
      -DWITH_PCAP=OFF -DWITH_NACL=OFF -DWITH_EXAMPLES=OFF -DWITH_ZLIB=ON; \
    cmake --build /build/libssh --target ssh_server_fuzzer --parallel 2; \
    cp -a /src/libssh/tests/fuzz/ssh_server_fuzzer_corpus /work/seeds; \
    { \
      printf 'target=libssh SSH server protocol parser\n'; \
      printf 'release=0.12.2\n'; \
      printf 'source_sha256=%s\n' '49560f677d96e3706a904ac2de1116e25f3680937d51e5c92198fcba4a1c1e9f'; \
      printf 'signature_primary_fingerprint=%s\n' '88A228D89B07C2C77D0C780903D5DF8CFDD3E8E7'; \
      printf 'fuzz_target=ssh_server_fuzzer\n'; \
      printf 'libfuzzer_coverage=enabled\naddress_sanitizer=enabled\nundefined_behavior_sanitizer=enabled\n'; \
      printf 'upstream_fuzz_testing=ON\nwith_insecure_none=ON (upstream requirement for repeatable SSH packet fuzzing)\nwith_exec=OFF\n'; \
      printf 'base_image=%s\n' 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852'; \
      clang --version | head -1; cmake --version | head -1; ninja --version; \
      grep -E '^(UNIT_TESTING|FUZZ_TESTING|WITH_SERVER|WITH_EXEC|WITH_INSECURE_NONE|BUILD_SHARED_LIBS|BUILD_STATIC_LIB):BOOL=' /build/libssh/CMakeCache.txt; \
      sha256sum /build/libssh/tests/fuzz/ssh_server_fuzzer; \
    } > /work/build-evidence/build-lock.txt; \
    rm -rf /tmp/libssh-gnupg /tmp/source

WORKDIR /work
ENTRYPOINT ["/work/run-container.sh"]
