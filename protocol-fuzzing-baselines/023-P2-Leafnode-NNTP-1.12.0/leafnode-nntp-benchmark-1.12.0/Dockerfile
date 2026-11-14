FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG LEAFNODE_VERSION=1.12.0
ARG LEAFNODE_SHA256=8310b78006a2088b82dcf9a6b18504ec4f7279bd1047af58d3dac5aaf607ce58
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0 \
    LEAFNODE_PREFIX=/opt/leafnode-afl

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\.ubuntu\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/$UBUNTU_SNAPSHOT/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake bison build-essential clang file flex gcovr git \
      graphviz graphviz-dev libpcre2-dev libtool llvm llvm-dev make perl pkg-config procps \
      python3 python3-minimal time util-linux && \
    rm -rf /var/lib/apt/lists/*

RUN getent group bench >/dev/null || groupadd --gid 1000 bench; \
    getent passwd bench >/dev/null || useradd --uid 1000 --gid bench \
      --create-home --shell /bin/bash bench

COPY source/leafnode-1.12.0.tar.xz /tmp/leafnode.tar.xz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-nntp.patch nntp_aflnet.c parser-test.c prepare_seeds.py \
     setup.py reset_spool.py leafnode-inetd-harness.patch listener.c \
     protocol_smoke.py coverage_replay.py run.sh nntp.dict /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/

RUN echo "$LEAFNODE_SHA256  /tmp/leafnode.tar.xz" | sha256sum -c - && \
    echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && \
    mkdir -p "$AFLNET" /tmp/leafnode-source && \
    tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && \
    tar -xJf /tmp/leafnode.tar.xz -C /tmp/leafnode-source --strip-components=1 && \
    sed -i 's/\r$//' "$AFLNET/Makefile" "$AFLNET/aflnet.h" \
      "$AFLNET/afl-fuzz.c" "$AFLNET/afl-replay.c" "$AFLNET/aflnet-replay.c" && \
    git -C "$AFLNET" init -q && \
    git -C "$AFLNET" apply --unidiff-zero --check /opt/benchmark/aflnet-nntp.patch && \
    git -C "$AFLNET" apply --unidiff-zero /opt/benchmark/aflnet-nntp.patch && \
    cp /opt/benchmark/nntp_aflnet.c "$AFLNET/nntp_aflnet.c" && \
    cd "$AFLNET" && make clean && make -j2 all && \
    cd llvm_mode && make -j2 && \
    cd "$AFLNET" && make nntp_aflnet.o && \
    cc -O2 -I"$AFLNET" /opt/benchmark/parser-test.c nntp_aflnet.o -o /tmp/nntp-parser-test && \
    /tmp/nntp-parser-test && \
    python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds /opt/benchmark/in-nntp

RUN set -eu; \
    for variant in reference afl gcov; do \
      mkdir -p "/tmp/leafnode-$variant"; \
      tar -xJf /tmp/leafnode.tar.xz -C "/tmp/leafnode-$variant" --strip-components=1; \
      cd "/tmp/leafnode-$variant"; \
      prefix="/opt/leafnode-$variant"; \
      case "$variant" in \
        reference) compiler=cc; cflags='-O2 -g'; ldflags='';; \
        afl) compiler="$AFLNET/afl-clang-fast"; cflags='-O1 -g -fno-omit-frame-pointer'; ldflags='';; \
        gcov) compiler=cc; cflags='-O0 -g --coverage'; ldflags='--coverage';; \
      esac; \
      git init -q; \
      git apply --unidiff-zero --check /opt/benchmark/leafnode-inetd-harness.patch; \
      git apply --unidiff-zero /opt/benchmark/leafnode-inetd-harness.patch; \
      cp /opt/benchmark/listener.c .; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 \
        ./configure --prefix="$prefix" --sysconfdir="$prefix/etc" \
        --localstatedir="$prefix/var" --with-user=bench --with-group=bench \
        --with-spooldir="$prefix/spool" --with-lockfile="$prefix/spool/leaf.node/lock.file"; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 make -j2; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 make install; \
    done; \
    python3 /opt/benchmark/setup.py; \
    chown -R bench:bench /opt/leafnode-reference /opt/leafnode-afl /opt/leafnode-gcov /tmp/leafnode-gcov; \
    chmod -R g+rwX /opt/leafnode-reference /opt/leafnode-afl /opt/leafnode-gcov /tmp/leafnode-gcov; \
    { \
      echo "base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214"; \
      echo "ubuntu_snapshot=$UBUNTU_SNAPSHOT"; \
      echo "leafnode_version=$LEAFNODE_VERSION"; \
      echo "leafnode_source_archive_sha256=$LEAFNODE_SHA256"; \
      echo "aflnet_commit=$AFLNET_COMMIT"; \
      echo "aflnet_archive_sha256=$AFLNET_SHA256"; \
      echo "nntp_adapter_sha256=$(sha256sum /opt/benchmark/nntp_aflnet.c | cut -d ' ' -f1)"; \
      for variant in reference afl gcov; do \
        echo "leafnode-$variant-sha256=$(sha256sum "/opt/leafnode-$variant/sbin/leafnode" | cut -d ' ' -f1)"; \
      done; \
      cc --version | sed -n '1p'; \
      clang --version | sed -n '1p'; \
      dpkg-query -W build-essential libpcre2-dev llvm make python3; \
    } > /opt/benchmark/build-versions.txt; \
    rm -rf /tmp/leafnode-source /tmp/leafnode-reference /tmp/leafnode-afl \
      /tmp/leafnode.tar.xz /tmp/aflnet.tar.gz /tmp/nntp-parser-test

WORKDIR /opt/benchmark
USER bench
CMD ["/opt/leafnode-afl/sbin/leafnode"]
