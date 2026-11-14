FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG MAKE_JOBS=1
ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    ASAN_OPTIONS=abort_on_error=1:detect_leaks=0:symbolize=0

RUN apt-get update && apt-get install -y --no-install-recommends \
      bison build-essential ca-certificates flex libgraphviz-dev m4 libncurses-dev \
      libpcre2-dev libssl-dev pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/*.tar.gz /tmp/
COPY source-checksums.sha256 /tmp/source-checksums.sha256
RUN cd /tmp && sha256sum -c source-checksums.sha256 \
    && mkdir -p /opt/aflnet /src/opensips \
    && tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet \
    && tar -xzf /tmp/opensips-4.0.3.tar.gz -C /src/opensips --strip-components=1 \
    && make -C /opt/aflnet -j${MAKE_JOBS} all

RUN cd /src/opensips \
    && make Makefile.conf \
    && sed -i \
      -e 's/^#*DEFS+= -DPKG_MALLOC/DEFS+= -DSYSTEM_MALLOC/' \
      -e 's/^DEFS+= -DUSE_MCAST/#DEFS+= -DUSE_MCAST/' \
      -e 's/^DEFS+= -DF_MALLOC/#DEFS+= -DF_MALLOC/' \
      -e 's/^DEFS+= -DQ_MALLOC/#DEFS+= -DQ_MALLOC/' \
      -e 's/^DEFS+= -DHP_MALLOC/#DEFS+= -DHP_MALLOC/' \
      -e 's/^DEFS+= -DDBG_MALLOC/#DEFS+= -DDBG_MALLOC/' \
      Makefile.conf \
    && AFL_DONT_OPTIMIZE=1 AFL_USE_ASAN=1 make -j${MAKE_JOBS} \
         CC=/opt/aflnet/afl-gcc CC_EXTRA_OPTS='-O1 -g -fno-omit-frame-pointer' opensips \
    && AFL_DONT_OPTIMIZE=1 AFL_USE_ASAN=1 make -j${MAKE_JOBS} \
         CC=/opt/aflnet/afl-gcc CC_EXTRA_OPTS='-O1 -g -fno-omit-frame-pointer' \
         module=sl modules \
    && ./opensips -V | grep -F '4.0.3'

COPY opensips.cfg generate_seeds.py validate.sh run.sh /work/
RUN python3 /work/generate_seeds.py /work/seeds \
    && chmod +x /work/validate.sh /work/run.sh \
    && mkdir -p /work/results /work/state \
    && chmod 0777 /work/results /work/state

WORKDIR /work
ENTRYPOINT ["/bin/bash"]
