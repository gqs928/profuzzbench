ARG FRR_IMAGE=quay.io/frrouting/frr:10.7.1@sha256:e995beaa50fdc9edb35eadcfefa29b7f062cc06f2b812613789b68fa541554d2

FROM ${FRR_IMAGE} AS afl_builder
USER root
RUN apk add --no-cache build-base linux-headers patch tar gzip graphviz-dev
COPY aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-network-noforkserver.patch aflnet-network-config-terminator.patch \
     aflnet-bgp.patch aflnet-alpine-portability.patch bgp_aflnet.inc \
     bgp-parser-test.c /tmp/bgp-adapter/
RUN set -eux; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' | sha256sum -c -; \
    mkdir -p /opt/aflnet; tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/bgp-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/bgp-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/bgp-adapter/aflnet-bgp.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/bgp-adapter/aflnet-bgp.patch; \
    patch --batch --fuzz=0 --dry-run -p1 -d /opt/aflnet -i /tmp/bgp-adapter/aflnet-network-config-terminator.patch; \
    patch --batch --fuzz=0 --forward -p1 -d /opt/aflnet -i /tmp/bgp-adapter/aflnet-network-config-terminator.patch; \
    patch --batch --fuzz=0 --dry-run -p1 -d /opt/aflnet -i /tmp/bgp-adapter/aflnet-alpine-portability.patch; \
    patch --batch --fuzz=0 --forward -p1 -d /opt/aflnet -i /tmp/bgp-adapter/aflnet-alpine-portability.patch; \
    cp /tmp/bgp-adapter/bgp_aflnet.inc /opt/aflnet/bgp_aflnet.inc; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    cc -std=c99 -O2 -Wall -Wextra -Werror /tmp/bgp-adapter/bgp-parser-test.c -o /tmp/bgp-parser-test; \
    /tmp/bgp-parser-test; \
    grep -a -q BGP /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /tmp/afl-fuzz-build-ldd.txt; \
    if grep -q 'not found' /tmp/afl-fuzz-build-ldd.txt; then exit 1; fi; \
    rm -rf /tmp/aflnet.tar.gz /tmp/bgp-adapter /tmp/bgp-parser-test

ARG FRR_IMAGE
FROM ${FRR_IMAGE} AS runtime
USER root
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 FRR_EXPECTED_VERSION=10.7.1 \
    BGP_HOST=127.0.0.1 BGP_PORT=179
RUN apk add --no-cache bash python3 graphviz-libs \
    && mkdir -p /opt/benchmark /usr/local/lib
COPY --from=afl_builder /opt/aflnet/ /opt/aflnet/
COPY --from=afl_builder /tmp/afl-fuzz-build-ldd.txt /opt/benchmark/afl-fuzz-build-ldd.txt
COPY README.md PACKAGE-MANIFEST.md ACCEPTANCE.md source-lock.json \
     aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
     aflnet-network-noforkserver.patch aflnet-bgp.patch \
     aflnet-network-config-terminator.patch aflnet-alpine-portability.patch bgp_aflnet.inc \
     bgp-parser-test.c prepare_seeds.py bgp_smoke.py replay_queue.py \
     deadline_wrapper.py start-bgpd.sh stop-bgpd.sh reset-bgpd.sh run.sh smoke.sh \
     bgpd.conf bgp.dict seeds-manifest.json /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
RUN set -eux; \
    ldconfig 2>/dev/null || true; \
    /usr/lib/frr/bgpd --version | tee /opt/benchmark/bgpd-version.txt; \
    grep -Fq '10.7.1_git' /opt/benchmark/bgpd-version.txt; \
    /usr/lib/frr/bgpd -C -f /opt/benchmark/bgpd.conf 2>&1 | tee /opt/benchmark/bgpd-config-check.txt; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    if grep -q 'not found' /opt/benchmark/afl-fuzz-runtime-ldd.txt; then exit 1; fi; \
    python3 -m py_compile /opt/benchmark/prepare_seeds.py /opt/benchmark/bgp_smoke.py \
      /opt/benchmark/replay_queue.py /opt/benchmark/deadline_wrapper.py; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py
WORKDIR /opt/benchmark
ENTRYPOINT []
