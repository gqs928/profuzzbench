FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_JOBS=1
ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    LD_LIBRARY_PATH=/opt/bind-afl/lib

RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake bison build-essential ca-certificates clang flex \
      graphviz-dev libcap-dev libedit-dev libjson-c-dev libkrb5-dev liblmdb-dev \
      libmaxminddb-dev libnghttp2-dev libssl-dev libtool liburcu-dev libuv1-dev \
      libxml2-dev llvm llvm-dev make perl pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY source/bind9-9.20.30.tar.gz /tmp/bind9.tar.gz
COPY source-checksums.sha256 /tmp/source-checksums.sha256

RUN cd /tmp && sha256sum -c source-checksums.sha256 \
    && mkdir -p /opt/aflnet /src/bind9 \
    && tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet \
    && tar -xzf /tmp/bind9.tar.gz -C /src/bind9 \
    && make -C /opt/aflnet -j${MAKE_JOBS} all \
    && cd /src/bind9 && autoreconf -fi

RUN useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin bindfuzz \
    && mkdir -p /work/state /work/results /opt/bind-afl \
    && chown -R bindfuzz:bindfuzz /work /src/bind9 /opt/aflnet /opt/bind-afl

USER bindfuzz
WORKDIR /work
RUN cd /src/bind9 \
    && CC=/opt/aflnet/afl-gcc \
       AFL_DONT_OPTIMIZE=1 \
       AFL_USE_ASAN=1 \
       CFLAGS='-O1 -g -fno-omit-frame-pointer' \
       ./configure --prefix=/opt/bind-afl --disable-static \
    && AFL_DONT_OPTIMIZE=1 AFL_USE_ASAN=1 make -j${MAKE_JOBS} \
    && make install \
    && /opt/bind-afl/sbin/named -V | grep -F 'BIND 9.20.30'

USER root
COPY named.conf zone.example seeds/generate_seeds.py /work/
COPY validate.sh run.sh /work/
RUN python3 /work/generate_seeds.py /work/seeds \
    && chown -R bindfuzz:bindfuzz /work \
    && chmod +x /work/validate.sh /work/run.sh \
    && chmod 0777 /work/state /work/results

ENV ASAN_OPTIONS=abort_on_error=1:detect_leaks=0:detect_stack_use_after_return=1:symbolize=0
USER bindfuzz

ENTRYPOINT ["/bin/bash"]
