FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG INN_VERSION=2.7.4
ARG INN_SHA256=80fc7e801e1996cb17bb430d104dd9c5b29aa571fd4b29a9c821b4fadb051d3b
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
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/$UBUNTU_SNAPSHOT/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake bison build-essential clang file flex g++ gcc gcovr git \
      graphviz graphviz-dev libdb-dev libssl-dev libsqlite3-dev libtool \
      libxml2-dev llvm llvm-dev make perl pkg-config procps python3 \
      python3-minimal time zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN getent group news >/dev/null || groupadd --gid 1000 news; \
    getent passwd news >/dev/null || useradd --uid 1000 --gid news \
      --create-home --shell /bin/bash news

COPY source/inn-2.7.4.tar.gz /tmp/inn.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-nntp.patch nntp_aflnet.c parser-test.c prepare_seeds.py \
     setup.py nntp.dict /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/

RUN echo "$INN_SHA256  /tmp/inn.tar.gz" | sha256sum -c - && \
    echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && \
    mkdir -p "$AFLNET" /tmp/inn-source && \
    tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && \
    tar -xzf /tmp/inn.tar.gz -C /tmp/inn-source --strip-components=1 && \
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
      mkdir -p "/tmp/inn-$variant"; \
      tar -xzf /tmp/inn.tar.gz -C "/tmp/inn-$variant" --strip-components=1; \
      cd "/tmp/inn-$variant"; \
      prefix="/opt/inn-$variant"; \
      case "$variant" in \
        reference) compiler=cc; cflags='-O2 -g'; ldflags='';; \
        afl) compiler="$AFLNET/afl-clang-fast"; cflags='-O1 -g -fno-omit-frame-pointer'; ldflags='';; \
        gcov) compiler=cc; cflags='-O0 -g --coverage'; ldflags='--coverage';; \
      esac; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 \
        ./configure --prefix="$prefix" --sysconfdir="$prefix/etc" \
        --localstatedir="$prefix/var" --with-news-user=news --with-news-group=news \
        --with-db-dir="$prefix/db" --with-spool-dir="$prefix/spool" \
        --with-log-dir="$prefix/log" --with-run-dir="$prefix/run" \
        --with-tmp-dir="$prefix/tmp" --with-openssl \
        --with-sendmail=/bin/true; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 make -j2; \
      CC="$compiler" CFLAGS="$cflags" LDFLAGS="$ldflags" AFL_USE_ASAN=1 make install; \
    done; \
    python3 /opt/benchmark/setup.py; \
    chown -R news:news /opt/inn-reference /opt/inn-afl /opt/inn-gcov; \
    for variant in reference afl gcov; do \
      su news -s /bin/sh -c "cd /opt/inn-$variant/db && /opt/inn-$variant/bin/makedbz -i -o"; \
    done; \
    { \
      echo 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214'; \
      echo "ubuntu_snapshot=$UBUNTU_SNAPSHOT"; \
      echo "inn_version=$INN_VERSION"; \
      echo "inn_source_archive_sha256=$INN_SHA256"; \
      echo "aflnet_commit=$AFLNET_COMMIT"; \
      echo "aflnet_archive_sha256=$AFLNET_SHA256"; \
      echo "aflnet_nntp_patch_sha256=$(sha256sum /opt/benchmark/aflnet-nntp.patch | cut -d ' ' -f1)"; \
      echo "nntp_adapter_sha256=$(sha256sum /opt/benchmark/nntp_aflnet.c | cut -d ' ' -f1)"; \
      for variant in reference afl gcov; do \
        echo "nnrpd-$variant-sha256=$(sha256sum "/opt/inn-$variant/bin/nnrpd" | cut -d ' ' -f1)"; \
      done; \
      cc --version | sed -n '1p'; \
      clang --version | sed -n '1p'; \
      dpkg-query -W build-essential graphviz libdb-dev libsqlite3-dev libssl-dev llvm make perl python3; \
    } > /opt/benchmark/build-versions.txt; \
    rm -rf /tmp/inn-source /tmp/inn-reference /tmp/inn-afl \
      /tmp/inn.tar.gz /tmp/aflnet.tar.gz /tmp/nntp-parser-test

RUN chown -R news:news /tmp/inn-gcov && \
    for variant in reference afl gcov; do \
      su news -s /bin/sh -c "/opt/inn-$variant/bin/makehistory -O -x -F"; \
    done && \
    find /tmp/inn-gcov -name '*.gcda' -delete && \
    chmod -R g+rwX /opt/inn-reference /opt/inn-afl /opt/inn-gcov /tmp/inn-gcov

COPY protocol_smoke.py coverage_replay.py run.sh /opt/benchmark/

WORKDIR /opt/benchmark
USER news
CMD ["/opt/inn-afl/bin/nnrpd", "-D", "-f", "-4", "127.0.0.1", "-p", "1119", "-n"]
