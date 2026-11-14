FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG MAKE_JOBS=2
ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    ASAN_OPTIONS=abort_on_error=1:detect_leaks=0:symbolize=0

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential ca-certificates graphviz libboost-dev libboost-system-dev \
      libgraphviz-dev liblog4cplus-dev libssl-dev meson ninja-build patch pkg-config \
      python3 \
    && rm -rf /var/lib/apt/lists/*

COPY source/*.tar.gz /tmp/
COPY source-checksums.sha256 /tmp/source-checksums.sha256
COPY aflnet-dhcp.patch /tmp/aflnet-dhcp.patch
COPY patch-checksums.sha256 /tmp/patch-checksums.sha256
RUN cd /tmp && sha256sum -c source-checksums.sha256 \
    && sha256sum -c patch-checksums.sha256 \
    && mkdir -p /opt/aflnet /src/kea /opt/kea \
    && tar -xzf aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet \
    && patch --binary -p1 -d /opt/aflnet < /tmp/aflnet-dhcp.patch \
    && tar -xzf kea-3.2.1.tar.gz -C /src/kea --strip-components=1 \
    && AFL_NO_X86=1 make -C /opt/aflnet -j${MAKE_JOBS} all

ENV CC=/opt/aflnet/afl-gcc \
    CXX=/opt/aflnet/afl-g++ \
    AFL_DONT_OPTIMIZE=1 \
    CFLAGS='-O1 -g -fno-omit-frame-pointer' \
    CXXFLAGS='-O1 -g -fno-omit-frame-pointer'

RUN cd /src/kea \
    && meson setup build --prefix=/opt/kea -Dcrypto=openssl -D fuzz=disabled -D tests=disabled \
         -D mysql=disabled -D postgresql=disabled -D krb5=disabled -D netconf=disabled \
    && meson compile -C build -j${MAKE_JOBS} kea-dhcp4 \
    && test -x /src/kea/build/src/bin/dhcp4/kea-dhcp4 \
    && find /src/kea/build/src/lib -type f -name 'libkea-*.so*' -printf '%h\n' | sort -u | paste -sd: > /opt/kea/build-libdirs

RUN mkdir -p /opt/kea/var/run/kea && chmod 1777 /opt/kea/var/run/kea

COPY kea.conf make_seeds.py validate.py run.sh triage_hangs.py kea-target.sh /work/
RUN python3 /work/make_seeds.py /work/seeds \
    && chmod +x /work/run.sh /work/validate.py /work/kea-target.sh \
    && mkdir -p /work/results \
    && chmod 0777 /work/results

WORKDIR /work
ENTRYPOINT ["/bin/bash"]
