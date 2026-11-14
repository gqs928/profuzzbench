ARG CASSANDRA_IMAGE=cassandra:5.0.9@sha256:7e2afd76d5afb991f64c5d9be7d1f8abf749e7ab0e9daaccfd6e865efcece7cc
FROM ${CASSANDRA_IMAGE}

ARG DEBIAN_SNAPSHOT=20261020T213255Z
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    MAX_HEAP_SIZE=512M \
    HEAP_NEWSIZE=128M

USER root
COPY aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-cassandra.patch aflnet-stateonly.patch cassandra_aflnet.inc \
     cassandra-parser-test.c aflnet.h alloc-inl.h /tmp/cassandra-adapter/

RUN set -eux; \
    printf '%s\n' \
      'Types: deb' \
      "URIs: http://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT}" \
      'Suites: trixie trixie-updates' \
      'Components: main' \
      'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
      '' \
      'Types: deb' \
      "URIs: http://snapshot.debian.org/archive/debian-security/${DEBIAN_SNAPSHOT}" \
      'Suites: trixie-security' \
      'Components: main' \
      'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
      > /etc/apt/sources.list.d/debian.sources; \
    apt-get update -o Acquire::Check-Valid-Until=false; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      bash build-essential ca-certificates coreutils findutils git libgraphviz-dev \
      libgvc6 patch procps tar gzip; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' \
      | sha256sum -c -; \
    mkdir -p /opt/aflnet /opt/benchmark/seeds /opt/benchmark/results; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h \
      /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c; \
    git -C /opt/aflnet apply --check /tmp/cassandra-adapter/aflnet-cassandra.patch; \
    git -C /opt/aflnet apply /tmp/cassandra-adapter/aflnet-cassandra.patch; \
    git -C /opt/aflnet apply --check /tmp/cassandra-adapter/aflnet-stateonly.patch; \
    git -C /opt/aflnet apply /tmp/cassandra-adapter/aflnet-stateonly.patch; \
    cp /tmp/cassandra-adapter/cassandra_aflnet.inc /opt/aflnet/cassandra_aflnet.inc; \
    AFL_NO_X86=1 make -C /opt/aflnet -j2 all afl-fuzz afl-replay aflnet-replay; \
    cc -O2 -Wall -Wextra -Werror -I/tmp/cassandra-adapter \
      /tmp/cassandra-adapter/cassandra-parser-test.c -o /tmp/cassandra-parser-test; \
    /tmp/cassandra-parser-test; \
    grep -a -q CASSANDRA /opt/aflnet/afl-fuzz; \
    apt-get purge -y build-essential git libgraphviz-dev patch; \
    apt-get autoremove -y; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/aflnet.tar.gz /tmp/cassandra-adapter /tmp/cassandra-parser-test

COPY . /opt/benchmark/
RUN set -eux; \
    apt-get update -o Acquire::Check-Valid-Until=false; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      build-essential libgraphviz-dev patch; \
    patch --dry-run -d /opt/aflnet -p1 < /opt/benchmark/aflnet-network-noforkserver.patch; \
    patch -d /opt/aflnet -p1 < /opt/benchmark/aflnet-network-noforkserver.patch; \
    AFL_NO_X86=1 make -C /opt/aflnet -j2 afl-fuzz; \
    apt-get purge -y build-essential libgraphviz-dev patch; \
    apt-get autoremove -y; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*
RUN chmod +x /opt/benchmark/*.sh
WORKDIR /opt/benchmark
ENTRYPOINT []
