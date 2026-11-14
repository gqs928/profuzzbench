ARG YUGABYTE_IMAGE=docker.io/yugabytedb/yugabyte:2026.1.3.0-b100@sha256:3d2c008625dbbe06879f96452d22afd39806d80bbcdedaa6364c2a5ae8893469
ARG AFL_BUILDER_IMAGE=docker.io/scylladb/scylla:2026.3.5@sha256:bd9eb6c94044a68ea27d8d382c3a0f267db227e6182ac9f3ad3e65a46b92db0d

FROM ${AFL_BUILDER_IMAGE} AS builder
USER root

RUN microdnf install -y \
      --disablerepo=scylladb-2026.3 \
      --disablerepo=scylladb-2026.3-noarch \
      --disablerepo=ubi-9-codeready-builder-rpms \
      gcc gcc-c++ make patch tar gzip \
    && rpm -qa | sort > /tmp/rpm-packages-at-build.txt

COPY graphviz-2.44.0-26.el9.x86_64.rpm graphviz-devel-2.44.0-26.el9.x86_64.rpm \
     rocky-linux-9-build-repo.key /tmp/
COPY aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-cassandra.patch aflnet-stateonly.patch aflnet-network-noforkserver.patch \
     cassandra_aflnet.inc cassandra-parser-test.c aflnet.h alloc-inl.h /tmp/yugabyte-adapter/

RUN set -eux; \
    rpm --import /tmp/rocky-linux-9-build-repo.key; \
    echo '31a674d1d3f543f7bd6d6da6694e3d267dbd1b04ca5e739ba0bdab6bc0411d97  /tmp/graphviz-2.44.0-26.el9.x86_64.rpm' | sha256sum -c -; \
    echo '1c48cd518a01e8fda8a20017424b35978de19761ecaf08a74f7a25582904b230  /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm' | sha256sum -c -; \
    rpm --checksig --verbose /tmp/graphviz-2.44.0-26.el9.x86_64.rpm; \
    rpm --checksig --verbose /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm; \
    rpm -Uvh --nodeps /tmp/graphviz-2.44.0-26.el9.x86_64.rpm; \
    rpm -q graphviz | grep -qx 'graphviz-2.44.0-26.el9.x86_64'; \
    rpm -Uvh --nodeps /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm; \
    ldconfig; \
    mkdir -p /opt/aflnet; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' | sha256sum -c -; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/yugabyte-adapter/aflnet-cassandra.patch; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/yugabyte-adapter/aflnet-stateonly.patch; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/yugabyte-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/yugabyte-adapter/aflnet-cassandra.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/yugabyte-adapter/aflnet-stateonly.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/yugabyte-adapter/aflnet-network-noforkserver.patch; \
    cp /tmp/yugabyte-adapter/cassandra_aflnet.inc /opt/aflnet/cassandra_aflnet.inc; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    cc -O2 -Wall -Wextra -Werror -I/tmp/yugabyte-adapter /tmp/yugabyte-adapter/cassandra-parser-test.c -o /tmp/cassandra-parser-test; \
    /tmp/cassandra-parser-test; \
    grep -a -q CASSANDRA /opt/aflnet/afl-fuzz; \
    ldd /opt/aflnet/afl-fuzz | tee /tmp/afl-fuzz-build-ldd.txt; \
    if grep -q 'not found' /tmp/afl-fuzz-build-ldd.txt; then exit 1; fi; \
    ldconfig; \
    mkdir -p /tmp/graphviz-runtime-libs; \
    cp -a /usr/lib64/libcgraph.so.6* /usr/lib64/libcdt.so.5* /usr/lib64/libgvc.so.6* \
      /usr/lib64/libpathplan.so.4* /usr/lib64/libxdot.so.4* /tmp/graphviz-runtime-libs/; \
    rm -rf /tmp/aflnet.tar.gz /tmp/yugabyte-adapter /tmp/cassandra-parser-test \
      /tmp/graphviz-2.44.0-26.el9.x86_64.rpm /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm \
      /tmp/rocky-linux-9-build-repo.key

FROM ${YUGABYTE_IMAGE} AS runtime
ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    YUGABYTE_EXPECTED_VERSION=2026.1.3.0 \
    YUGABYTE_EXPECTED_BUILD=100 \
    YCQL_PORT=9042

USER root
COPY --from=builder /opt/aflnet/ /opt/aflnet/
COPY --from=builder /tmp/graphviz-runtime-libs/ /usr/lib64/
COPY --from=builder /tmp/rpm-packages-at-build.txt /tmp/rpm-packages-at-build.txt
COPY --from=builder /tmp/afl-fuzz-build-ldd.txt /tmp/afl-fuzz-build-ldd.txt
COPY . /opt/benchmark/
RUN set -eux; \
    mkdir -p /opt/benchmark/build-logs; \
    cp /tmp/rpm-packages-at-build.txt /opt/benchmark/build-logs/rpm-packages-at-build.txt; \
    cp /tmp/afl-fuzz-build-ldd.txt /opt/benchmark/build-logs/afl-fuzz-build-ldd.txt; \
    ldconfig; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/build-logs/afl-fuzz-runtime-ldd.txt; \
    if grep -q 'not found' /opt/benchmark/build-logs/afl-fuzz-runtime-ldd.txt; then exit 1; fi; \
    chmod +x /opt/benchmark/*.sh
WORKDIR /opt/benchmark
ENTRYPOINT []
