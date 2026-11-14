ARG BASE_IMAGE=docker.io/library/ubuntu:26.04@sha256:065aa8626841f16057b78b027b464cd59c4fac36c204c72dcbf48d66f5fa8a96
FROM ${BASE_IMAGE}
ARG DEBIAN_FRONTEND=noninteractive
ARG PJPROJECT_SHA256=04b2eb1f0f01aa0ad1945b167171843448a51aa6b7c3e806496d434f13a112b7
ENV CC=clang CXX=clang++ \
    CFLAGS="-O1 -g -fno-omit-frame-pointer -fsanitize=fuzzer-no-link,address" \
    CXXFLAGS="-O1 -g -fno-omit-frame-pointer -fsanitize=fuzzer-no-link,address" \
    LDFLAGS="-fsanitize=address" \
    ASAN_OPTIONS="abort_on_error=1:symbolize=0:detect_leaks=0"
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential clang libclang-rt-dev ca-certificates bzip2 make pkg-config \
      libssl-dev zlib1g-dev libasound2-dev unzip python3 \
    && rm -rf /var/lib/apt/lists/*
COPY source/pjproject-2.17.tar.bz2 /tmp/pjproject-2.17.tar.bz2
RUN echo "${PJPROJECT_SHA256}  /tmp/pjproject-2.17.tar.bz2" | sha256sum -c - \
    && tar -xjf /tmp/pjproject-2.17.tar.bz2 -C /opt \
    && rm /tmp/pjproject-2.17.tar.bz2
WORKDIR /opt/pjproject-2.17
RUN ./configure --disable-sound --disable-video \
    && make dep -j2 \
    && make -j2
COPY Makefile.native /opt/pjproject-2.17/tests/fuzz/Makefile.native
RUN make -C tests/fuzz -f Makefile.native CC=clang CXX=clang++ fuzz-sip \
    && install -d /opt/benchmark/seeds /opt/benchmark/build-logs \
    && unzip -q -j tests/fuzz/seed/fuzz-sip_seed_corpus.zip '*.sip' -d /opt/benchmark/seeds \
    && install tests/fuzz/fuzz-sip /opt/benchmark/fuzz-sip \
    && dpkg-query -W -f='${Package}=${Version}\n' clang libclang-rt-dev libssl-dev python3 > /opt/benchmark/build-logs/build-packages.txt \
    && clang --version > /opt/benchmark/build-logs/clang-version.txt \
    && ldd /opt/benchmark/fuzz-sip | tee /opt/benchmark/build-logs/fuzz-sip-ldd.txt \
    && ! grep -F 'not found' /opt/benchmark/build-logs/fuzz-sip-ldd.txt
COPY run-container.sh summarize_fuzz_log.py /opt/benchmark/
RUN chmod 755 /opt/benchmark/run-container.sh \
    && test -x /opt/benchmark/fuzz-sip
WORKDIR /opt/benchmark
CMD ["/bin/bash"]
