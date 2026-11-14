FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG ERGO_VERSION=2.19.1
ARG ERGO_SHA256=7b1f6fac874a75c766ccd41d068f4408ac09aa30e594233afe87e7793d93c587
ARG GO_VERSION=1.27.3
ARG GO_SHA256=65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40
ARG QEMU_SHA384=68216c935487bc8c0596ac309e1e3ee75c2c4ce898aab796faa321db5740609ced365fedda025678d072d09ac8928105
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    GOTOOLCHAIN=local

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 && \
    apt-get install -y -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/$UBUNTU_SNAPSHOT/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 && \
    apt-get install -y -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 --no-install-recommends \
      autoconf automake bison build-essential ca-certificates file flex git \
      graphviz graphviz-dev libglib2.0-dev libpixman-1-dev libtool libtool-bin make patch \
      perl pkg-config python2.7 python3 python3-minimal time wget xz-utils zlib1g-dev && \
    ln -sf /usr/bin/python2.7 /usr/local/bin/python && \
    rm -rf /var/lib/apt/lists/*

COPY source/ergo-v2.19.1.tar.gz /tmp/ergo.tar.gz
COPY source/go1.27.3.linux-amd64.tar.gz /tmp/go.tar.gz
COPY source/qemu-2.10.0.tar.xz /tmp/qemu-2.10.0.tar.xz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-irc.patch irc_aflnet.c parser-test.c prepare_seeds.py \
     make_config.py irc.dict /opt/benchmark/
COPY qemu-2.10.0-modern-linux.patch /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/

RUN echo "$ERGO_SHA256  /tmp/ergo.tar.gz" | sha256sum -c - && \
    echo "$GO_SHA256  /tmp/go.tar.gz" | sha256sum -c - && \
    echo "$QEMU_SHA384  /tmp/qemu-2.10.0.tar.xz" | sha384sum -c - && \
    echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && \
    mkdir -p "$AFLNET" /opt/go /opt/ergo-source && \
    tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && \
    tar -xzf /tmp/ergo.tar.gz -C /opt/ergo-source --strip-components=1 && \
    tar -xzf /tmp/go.tar.gz -C /opt/go --strip-components=1 && \
    ln -s /opt/go/bin/go /usr/local/bin/go && \
    ln -s /opt/go/bin/gofmt /usr/local/bin/gofmt && \
    sed -i 's/\r$//' "$AFLNET/Makefile" "$AFLNET/aflnet.h" \
      "$AFLNET/afl-fuzz.c" "$AFLNET/afl-replay.c" "$AFLNET/aflnet-replay.c" \
      "$AFLNET/qemu_mode/build_qemu_support.sh" && \
    git -C "$AFLNET" init -q && \
    git -C "$AFLNET" apply --unidiff-zero --check /opt/benchmark/aflnet-irc.patch && \
    git -C "$AFLNET" apply --unidiff-zero /opt/benchmark/aflnet-irc.patch && \
    cp /opt/benchmark/irc_aflnet.c "$AFLNET/irc_aflnet.c" && \
    cd "$AFLNET" && make clean && make -j2 all && make irc_aflnet.o && \
    cc -O2 -I"$AFLNET" /opt/benchmark/parser-test.c irc_aflnet.o -o /tmp/irc-parser-test && \
    /tmp/irc-parser-test && \
    python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds /opt/benchmark/in-irc && \
    cd "$AFLNET/qemu_mode" && \
    cp /tmp/qemu-2.10.0.tar.xz . && \
    cp /opt/benchmark/qemu-2.10.0-modern-linux.patch patches/qemu-modern-linux.diff && \
    sed -i '/patch -p1 <..\/patches\/memfd.diff/a patch -p1 <../patches/qemu-modern-linux.diff || exit 1' build_qemu_support.sh && \
    ./build_qemu_support.sh && \
    test -x "$AFLNET/afl-qemu-trace" && \
    rm -rf qemu-2.10.0.tar.xz qemu-2.10.0

COPY aflnet-dumb-mode-network.patch aflnet-dumb-mode-state-feedback.patch \
     /opt/benchmark/
RUN git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-network.patch && \
    git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-network.patch && \
    git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && \
    git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && \
    make -C "$AFLNET" -j2 afl-fuzz

RUN set -eu; \
    cd /opt/ergo-source; \
    export PATH=/opt/go/bin:$PATH GOTOOLCHAIN=local CGO_ENABLED=0; \
    mkdir -p /opt/ergo-reference /opt/ergo-afl /opt/ergo-gcov; \
    for variant in reference afl; do \
      go build -trimpath -tags 'i18n mysql postgresql sqlite' \
        -ldflags '-s -w -X main.commit=7b1f6fac874a75c766ccd41d068f4408ac09aa30e594233afe87e7793d93c587 -X main.version=v2.19.1' \
        -o "/opt/ergo-$variant/ergo" .; \
    done; \
    go build -trimpath -tags 'i18n mysql postgresql sqlite' -cover -coverpkg=./... \
      -ldflags '-s -w -X main.commit=7b1f6fac874a75c766ccd41d068f4408ac09aa30e594233afe87e7793d93c587 -X main.version=v2.19.1' \
      -o /opt/ergo-gcov/ergo .; \
    mkdir -p /opt/benchmark/languages /opt/benchmark/configs; \
    cp -a languages/. /opt/benchmark/languages/; \
    python3 /opt/benchmark/make_config.py default.yaml /opt/benchmark/configs/ergo.yaml; \
    { \
      echo "base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214"; \
      echo "ubuntu_snapshot=$UBUNTU_SNAPSHOT"; \
      echo "ergo_version=$ERGO_VERSION"; \
      echo "ergo_source_archive_sha256=$ERGO_SHA256"; \
      echo "go_version=$GO_VERSION"; \
      echo "go_archive_sha256=$GO_SHA256"; \
      echo "aflnet_commit=$AFLNET_COMMIT"; \
      echo "aflnet_archive_sha256=$AFLNET_SHA256"; \
      echo "qemu_version=2.10.0"; \
      echo "qemu_archive_sha384=$QEMU_SHA384"; \
      echo "qemu_compatibility_patch_sha256=$(sha256sum /opt/benchmark/qemu-2.10.0-modern-linux.patch | cut -d ' ' -f1)"; \
      echo "aflnet_dumb_mode_network_patch_sha256=$(sha256sum /opt/benchmark/aflnet-dumb-mode-network.patch | cut -d ' ' -f1)"; \
      echo "aflnet_dumb_mode_state_feedback_patch_sha256=$(sha256sum /opt/benchmark/aflnet-dumb-mode-state-feedback.patch | cut -d ' ' -f1)"; \
      echo "fuzz_feedback=AFLNet IRC response states (-n); Go coverage collected separately with GOCOVERDIR"; \
      echo "irc_adapter_sha256=$(sha256sum /opt/benchmark/irc_aflnet.c | cut -d ' ' -f1)"; \
      for variant in reference afl gcov; do \
        echo "ergo-$variant-sha256=$(sha256sum "/opt/ergo-$variant/ergo" | cut -d ' ' -f1)"; \
      done; \
      go version; \
      cc --version | sed -n '1p'; \
      dpkg-query -W build-essential libglib2.0-dev libpixman-1-dev python2.7; \
    } > /opt/benchmark/build-versions.txt; \
    rm -rf /tmp/ergo.tar.gz /tmp/go.tar.gz \
      /tmp/qemu-2.10.0.tar.xz /tmp/aflnet.tar.gz /tmp/irc-parser-test

COPY protocol_smoke.py coverage_replay.py run.sh ergo-target.sh /opt/benchmark/
RUN chmod +x /opt/benchmark/run.sh /opt/benchmark/ergo-target.sh && \
    mkdir -p /tmp/ergo-data && chmod 1777 /tmp/ergo-data

WORKDIR /opt/benchmark
CMD ["/opt/benchmark/ergo-target.sh", "run", "--conf", "/opt/benchmark/configs/ergo.yaml"]
