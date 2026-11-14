ARG HTTPD_BASE_IMAGE=docker.io/library/ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${HTTPD_BASE_IMAGE} AS build
ARG HTTPD_VERSION=2.4.71
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      autoconf automake bash build-essential ca-certificates libapr1-dev \
      libaprutil1-dev libgraphviz-dev libnghttp2-dev libpcre2-dev libtool \
      pkg-config python3 python3-h2 zlib1g-dev patch \
    && rm -rf /var/lib/apt/lists/*
COPY source/ /opt/benchmark/source/
COPY patches/aflnet-http2.patch /opt/benchmark/patches/aflnet-http2.patch
COPY patches/aflnet-no-forkserver-reap.patch /opt/benchmark/patches/aflnet-no-forkserver-reap.patch
RUN set -eux; \
    echo '2bc5da5a33c247341de082717d4ebcb5cb49e8b73a05b7fddf7d5d6dc2f8de62  /opt/benchmark/source/httpd-2.4.71.tar.bz2' | sha256sum -c -; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz' | sha256sum -c -; \
    echo '270d112170703889cf548c4bf86d266987d2b7a2cc8a38b6c8261740821c42d1  /opt/benchmark/patches/aflnet-http2.patch' | sha256sum -c -; \
    echo '800de494fce15d9e8c53c9bd136c95a02207e5d3f72de8037cfb563072c9fe98  /opt/benchmark/patches/aflnet-no-forkserver-reap.patch' | sha256sum -c -; \
    mkdir -p /opt/aflnet /opt/httpd; \
    tar -xzf /opt/benchmark/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/aflnet.c /opt/aflnet/afl-fuzz.c; \
    patch -d /opt/aflnet -p0 < /opt/benchmark/patches/aflnet-http2.patch; \
    patch --batch --fuzz=0 -d /opt/aflnet -p0 < /opt/benchmark/patches/aflnet-no-forkserver-reap.patch; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    grep -a -q HTTP2 /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-build-ldd.txt
RUN set -eux; \
    tar -xjf /opt/benchmark/source/httpd-${HTTPD_VERSION}.tar.bz2 -C /tmp; \
    cd /tmp/httpd-${HTTPD_VERSION}; \
    CC=/opt/aflnet/afl-gcc CFLAGS='-O1 -g -fno-omit-frame-pointer' \
      ./configure --prefix=/opt/httpd --enable-so --enable-http2=shared \
      --enable-mods-shared=most --enable-mpms-shared=all --with-mpm=prefork \
      --with-nghttp2=/usr; \
    make -j2; \
    make install; \
    /opt/httpd/bin/httpd -v | tee /opt/benchmark/httpd-version.txt; \
    grep -Fq 'Apache/2.4.71' /opt/benchmark/httpd-version.txt; \
    ldd /opt/httpd/bin/httpd | tee /opt/benchmark/httpd-build-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/httpd-build-ldd.txt
RUN nm /opt/httpd/bin/httpd | grep -F '__afl_area_ptr' >/dev/null

FROM ${HTTPD_BASE_IMAGE} AS runtime
ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 HTTPD_PORT=20240
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash ca-certificates iproute2 libapr1 libaprutil1 libgvc6 libnghttp2-14 \
      libpcre2-8-0 python3 python3-h2 zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/benchmark /opt/httpd /opt/aflnet /opt/benchmark/www /results \
    && chmod 0777 /results
COPY --from=build /opt/httpd/ /opt/httpd/
COPY --from=build /opt/aflnet/ /opt/aflnet/
COPY --from=build /opt/benchmark/afl-fuzz-build-ldd.txt /opt/benchmark/
COPY --from=build /opt/benchmark/httpd-version.txt /opt/benchmark/
COPY --from=build /opt/benchmark/httpd-build-ldd.txt /opt/benchmark/
COPY httpd.conf /opt/benchmark/httpd.conf
COPY www/ /opt/benchmark/www/
COPY source-lock.json target-version.txt README.md PACKAGE-MANIFEST.md ACCEPTANCE.md \
     make_seeds.py protocol_smoke.py prepare-target.sh stop-target.sh \
     target.sh verify_listener_closed.py validate_seeds.py replay_queue.py deadline_wrapper.py \
     preflight.sh run.sh /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
RUN set -eux; \
    ldconfig; \
    /opt/httpd/bin/httpd -t -f /opt/benchmark/httpd.conf; \
    /opt/httpd/bin/httpd -M -f /opt/benchmark/httpd.conf | tee /opt/benchmark/httpd-modules.txt; \
    grep -q 'mpm_prefork_module' /opt/benchmark/httpd-modules.txt; \
    grep -q 'unixd_module' /opt/benchmark/httpd-modules.txt; \
    grep -q 'http2_module' /opt/benchmark/httpd-modules.txt; \
    ldd /opt/httpd/bin/httpd | tee /opt/benchmark/httpd-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/httpd-runtime-ldd.txt; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    ! grep -q 'not found' /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    python3 -m py_compile /opt/benchmark/make_seeds.py /opt/benchmark/protocol_smoke.py \
      /opt/benchmark/verify_listener_closed.py /opt/benchmark/validate_seeds.py \
      /opt/benchmark/replay_queue.py \
      /opt/benchmark/deadline_wrapper.py; \
    bash -n /opt/benchmark/prepare-target.sh /opt/benchmark/stop-target.sh /opt/benchmark/target.sh \
      /opt/benchmark/preflight.sh /opt/benchmark/run.sh; \
    python3 /opt/benchmark/make_seeds.py /opt/benchmark/seeds; \
    python3 /opt/benchmark/validate_seeds.py /opt/benchmark/seeds; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py
USER root
WORKDIR /opt/httpd
ENTRYPOINT []
