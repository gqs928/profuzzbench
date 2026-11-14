FROM docker.redpanda.com/redpandadata/redpanda:v26.2.6@sha256:8b1076e0d61bfceb66594dc01536427ce0b529f8ead35fdab9763ab6085891ce

ARG DEBIAN_SNAPSHOT=20261020T213255Z
USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Keep build tools from the same Debian snapshot embedded in the official image.
RUN set -eux; \
    printf '%s\n' \
      'Types: deb' \
      "URIs: https://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT}" \
      'Suites: trixie trixie-updates' \
      'Components: main' \
      'Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp' \
      '' \
      'Types: deb' \
      "URIs: https://snapshot.debian.org/archive/debian-security/${DEBIAN_SNAPSHOT}" \
      'Suites: trixie-security' \
      'Components: main' \
      'Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp' \
      > /etc/apt/sources.list.d/debian.sources; \
    apt-get update -o Acquire::Check-Valid-Until=false; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      build-essential ca-certificates coreutils findutils git libgraphviz-dev make python3 procps; \
    rm -rf /var/lib/apt/lists/*

ENV AFLNET=/home/redpanda/aflnet \
    AFL_PATH=/home/redpanda/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    WORKDIR=/home/redpanda/benchmark

RUN mkdir -p /home/redpanda/aflnet /home/redpanda/benchmark /home/redpanda/benchmark/results \
    && chown -R redpanda:redpanda /home/redpanda/aflnet /home/redpanda/benchmark
USER redpanda
WORKDIR /home/redpanda/benchmark

COPY --chown=redpanda:redpanda aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=redpanda:redpanda aflnet-kafka.patch aflnet-kafka-fuzz.patch kafka_aflnet.c parser-test.c test-stubs/ /tmp/redpanda-adapter/
RUN set -eux; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' | sha256sum -c -; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h "${AFLNET}"/afl-fuzz.c \
      "${AFLNET}"/afl-replay.c "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/redpanda-adapter/kafka_aflnet.c "${AFLNET}/kafka_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/redpanda-adapter/aflnet-kafka.patch; \
    git -C "${AFLNET}" apply /tmp/redpanda-adapter/aflnet-kafka.patch; \
    git -C "${AFLNET}" apply --check /tmp/redpanda-adapter/aflnet-kafka-fuzz.patch; \
    git -C "${AFLNET}" apply /tmp/redpanda-adapter/aflnet-kafka-fuzz.patch; \
    AFL_NO_X86=1 make -C "${AFLNET}" -j2 all afl-fuzz afl-replay aflnet-replay; \
    cc -O2 -Wall -Wextra -Werror \
      -I/tmp/redpanda-adapter/test-stubs -I"${AFLNET}" \
      /tmp/redpanda-adapter/parser-test.c \
      /tmp/redpanda-adapter/kafka_aflnet.c -o /tmp/kafka-parser-test; \
    /tmp/kafka-parser-test; \
    grep -a -q KAFKA "${AFLNET}/afl-fuzz"

COPY --chown=redpanda:redpanda . /home/redpanda/benchmark/
RUN set -eux; \
    chmod +x /home/redpanda/benchmark/*.sh; \
    AFL_QUIET=1 "${AFLNET}/afl-gcc" -O2 -g -Wall -Wextra -Werror \
      -o /home/redpanda/benchmark/redpanda-launcher \
      /home/redpanda/benchmark/redpanda_launcher.c; \
    /usr/bin/rpk --version | tee /home/redpanda/benchmark/redpanda-cli-version.txt; \
    /usr/bin/redpanda --version | tee /home/redpanda/benchmark/redpanda-server-version.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort \
      > /home/redpanda/benchmark/build-package-manifest.txt; \
    sha256sum /home/redpanda/aflnet/afl-fuzz \
      /home/redpanda/benchmark/redpanda-launcher \
      /home/redpanda/benchmark/kafka_aflnet.c \
      > /home/redpanda/benchmark/build-binaries.sha256

ENTRYPOINT []
