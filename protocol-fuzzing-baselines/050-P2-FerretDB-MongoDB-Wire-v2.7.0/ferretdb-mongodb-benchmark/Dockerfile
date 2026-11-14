ARG FERRETDB_IMAGE=ghcr.io/ferretdb/ferretdb:2.7.0@sha256:5706414241eb84f0515512c37b46db0f1b1eac9e5ceb7e4c2523211c184b1985
ARG DEBIAN_IMAGE=debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2
FROM ${FERRETDB_IMAGE} AS ferretdb_release

FROM ${DEBIAN_IMAGE}

ARG DEBIAN_SNAPSHOT=20261020T213255Z
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1

COPY --from=ferretdb_release /ferretdb /usr/local/bin/ferretdb
COPY aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-mongodb.patch aflnet-mongodb-fuzz.patch aflnet-stateonly.patch mongodb_aflnet.c \
     mongo-parser-test.c test-stubs/ /tmp/mongodb-adapter/

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
      libgvc6 patch postgresql-client procps python3 tar gzip; \
    apt-mark manual libgvc6; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' \
      | sha256sum -c -; \
    mkdir -p /opt/aflnet /opt/benchmark/seeds /opt/benchmark/results; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h \
      /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    git -C /opt/aflnet apply --check /tmp/mongodb-adapter/aflnet-mongodb.patch; \
    git -C /opt/aflnet apply /tmp/mongodb-adapter/aflnet-mongodb.patch; \
    git -C /opt/aflnet apply --check /tmp/mongodb-adapter/aflnet-mongodb-fuzz.patch; \
    git -C /opt/aflnet apply /tmp/mongodb-adapter/aflnet-mongodb-fuzz.patch; \
    git -C /opt/aflnet apply --check /tmp/mongodb-adapter/aflnet-stateonly.patch; \
    git -C /opt/aflnet apply /tmp/mongodb-adapter/aflnet-stateonly.patch; \
    cp /tmp/mongodb-adapter/mongodb_aflnet.c /opt/aflnet/mongodb_aflnet.c; \
    AFL_NO_X86=1 make -C /opt/aflnet -j2 all afl-fuzz afl-replay aflnet-replay; \
    cc -O2 -Wall -Wextra -Werror -I/tmp/mongodb-adapter/test-stubs \
      /tmp/mongodb-adapter/mongo-parser-test.c \
      /tmp/mongodb-adapter/mongodb_aflnet.c -o /tmp/mongo-parser-test; \
    /tmp/mongo-parser-test; \
    grep -a -q MONGODB /opt/aflnet/afl-fuzz; \
    apt-get purge -y build-essential git libgraphviz-dev patch; \
    apt-get autoremove -y; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/aflnet.tar.gz /tmp/mongodb-adapter /tmp/mongo-parser-test; \
    ldd /opt/aflnet/afl-fuzz | tee /tmp/aflnet-runtime-libraries.txt; \
    ! grep -q 'not found' /tmp/aflnet-runtime-libraries.txt; \
    rm /tmp/aflnet-runtime-libraries.txt; \
    useradd --system --uid 10001 --home-dir /home/ferretdb --create-home \
      --shell /usr/sbin/nologin ferretdb; \
    chown -R ferretdb:ferretdb /opt/aflnet /opt/benchmark /home/ferretdb

COPY . /opt/benchmark/
RUN set -eux; \
    chmod +x /opt/benchmark/*.sh; \
    /usr/local/bin/ferretdb --version | tee /opt/benchmark/ferretdb-version.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort \
      > /opt/benchmark/build-package-manifest.txt; \
    sha256sum /opt/aflnet/afl-fuzz /usr/local/bin/ferretdb \
      /opt/benchmark/mongodb_aflnet.c > /opt/benchmark/build-binaries.sha256; \
    chown -R ferretdb:ferretdb /opt/benchmark /opt/aflnet

USER ferretdb
WORKDIR /opt/benchmark
ENTRYPOINT []
