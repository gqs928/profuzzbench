FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG UNREALIRCD_VERSION=6.2.7.1
ARG UNREALIRCD_SHA256=4e372ba071f3211d34c5a3515af77fc2b275eb692e43e55c423e201b60958c3f
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\.ubuntu\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/$UBUNTU_SNAPSHOT/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake bison build-essential clang file flex gcovr git \
      graphviz graphviz-dev libargon2-0-dev libc-ares-dev libjansson-dev \
      libpcre2-dev libsodium-dev libssl-dev libtool llvm llvm-dev make perl \
      pkg-config procps python3 python3-minimal time zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN getent group bench >/dev/null || groupadd --gid 1000 bench; \
    getent passwd bench >/dev/null || useradd --uid 1000 --gid bench \
      --create-home --shell /bin/bash bench

COPY source/unrealircd-6.2.7.1.tar.gz /tmp/unrealircd.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-irc.patch irc_aflnet.c parser-test.c prepare_seeds.py \
     make_config.py setup.py irc.dict /opt/benchmark/
COPY configs/unrealircd.conf /opt/benchmark/configs/unrealircd.conf
COPY certs/ /opt/benchmark/certs/
COPY seeds/ /opt/benchmark/seeds/

RUN echo "$UNREALIRCD_SHA256  /tmp/unrealircd.tar.gz" | sha256sum -c - && \
    echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && \
    mkdir -p "$AFLNET" /tmp/unreal-source && \
    tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && \
    tar -xzf /tmp/unrealircd.tar.gz -C /tmp/unreal-source --strip-components=1 && \
    sed -i 's/\r$//' "$AFLNET/Makefile" "$AFLNET/aflnet.h" \
      "$AFLNET/afl-fuzz.c" "$AFLNET/afl-replay.c" "$AFLNET/aflnet-replay.c" && \
    git -C "$AFLNET" init -q && \
    git -C "$AFLNET" apply --unidiff-zero --check /opt/benchmark/aflnet-irc.patch && \
    git -C "$AFLNET" apply --unidiff-zero /opt/benchmark/aflnet-irc.patch && \
    cp /opt/benchmark/irc_aflnet.c "$AFLNET/irc_aflnet.c" && \
    cd "$AFLNET" && make clean && make -j2 all && \
    cd llvm_mode && make -j2 && \
    cd "$AFLNET" && make irc_aflnet.o && \
    cc -O2 -I"$AFLNET" /opt/benchmark/parser-test.c irc_aflnet.o -o /tmp/irc-parser-test && \
    /tmp/irc-parser-test && \
    python3 /opt/benchmark/prepare_seeds.py /opt/benchmark/seeds /opt/benchmark/in-irc

RUN set -eu; \
    for variant in reference afl gcov; do \
      mkdir -p "/tmp/unreal-$variant"; \
      tar -xzf /tmp/unrealircd.tar.gz -C "/tmp/unreal-$variant" --strip-components=1; \
      cd "/tmp/unreal-$variant"; \
      prefix="/opt/unreal-$variant"; \
      case "$variant" in \
        reference) compiler=cc; cflags='-O2 -g'; ldflags='';; \
        afl) compiler="$AFLNET/afl-clang-fast"; cflags='-O1 -g -fno-omit-frame-pointer'; ldflags='';; \
        gcov) compiler=cc; cflags='-O0 -g --coverage'; ldflags='--coverage';; \
      esac; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 \
        ./configure --with-bindir="$prefix/bin" --with-scriptdir="$prefix" \
        --with-datadir="$prefix/data" --with-pidfile="$prefix/data/unrealircd.pid" \
        --with-controlfile="$prefix/data/unrealircd.ctl" --with-confdir="$prefix/conf" \
        --with-modulesdir="$prefix/modules" --with-logdir="$prefix/logs" \
        --with-cachedir="$prefix/cache" --with-docdir="$prefix/doc" \
        --with-tmpdir="$prefix/tmp" --with-privatelibdir="$prefix/lib" \
        --with-maxconnections=1024 --with-permissions=0700 \
        --enable-dynamic-linking --enable-ssl=/usr --with-system-argon2 \
        --enable-geoip-classic=no --enable-mmdb=no; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 make -j2; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 make install; \
    done; \
    python3 /opt/benchmark/setup.py /opt/unreal-reference /opt/unreal-afl /opt/unreal-gcov; \
    chown -R bench:bench /opt/unreal-reference /opt/unreal-afl /opt/unreal-gcov /tmp/unreal-gcov; \
    chmod -R g+rwX /opt/unreal-reference /opt/unreal-afl /opt/unreal-gcov /tmp/unreal-gcov; \
    { \
      echo "base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214"; \
      echo "ubuntu_snapshot=$UBUNTU_SNAPSHOT"; \
      echo "unrealircd_version=$UNREALIRCD_VERSION"; \
      echo "unrealircd_source_archive_sha256=$UNREALIRCD_SHA256"; \
      echo "aflnet_commit=$AFLNET_COMMIT"; \
      echo "aflnet_archive_sha256=$AFLNET_SHA256"; \
      echo "irc_adapter_sha256=$(sha256sum /opt/benchmark/irc_aflnet.c | cut -d ' ' -f1)"; \
      for variant in reference afl gcov; do \
        echo "unrealircd-$variant-sha256=$(sha256sum "/opt/unreal-$variant/bin/unrealircd" | cut -d ' ' -f1)"; \
      done; \
      cc --version | sed -n '1p'; \
      clang --version | sed -n '1p'; \
      dpkg-query -W build-essential libpcre2-dev libssl-dev llvm make python3; \
    } > /opt/benchmark/build-versions.txt; \
    rm -rf /tmp/unreal-source /tmp/unreal-reference /tmp/unreal-afl \
      /tmp/unrealircd.tar.gz /tmp/aflnet.tar.gz /tmp/irc-parser-test

WORKDIR /opt/benchmark
COPY protocol_smoke.py coverage_replay.py run.sh /opt/benchmark/
COPY configs/unrealircd-tls.conf /opt/benchmark/configs/unrealircd-tls.conf
COPY setup_tls.py /opt/benchmark/setup_tls.py
RUN python3 /opt/benchmark/setup_tls.py \
      /opt/unreal-reference /opt/unreal-afl /opt/unreal-gcov
USER bench
CMD ["/opt/unreal-afl/bin/unrealircd", "-F", "-f", "/opt/unreal-afl/conf/unrealircd.conf"]
