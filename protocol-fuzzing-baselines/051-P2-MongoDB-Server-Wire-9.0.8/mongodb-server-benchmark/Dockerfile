ARG MONGO_IMAGE=mongo:9.0.8
FROM ${MONGO_IMAGE}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    HOME=/tmp

WORKDIR /opt/benchmark
COPY aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-graphviz-bool.patch aflnet-mongodb.patch aflnet-mongodb-fuzz.patch aflnet-stateonly.patch \
     mongodb_aflnet.c mongo-parser-test.c mongo-target-hold.c test-stubs/ /tmp/mongodb-adapter/

RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      bash build-essential ca-certificates coreutils findutils git libgraphviz-dev \
      patch procps python3; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' \
      | sha256sum -c -; \
    mkdir -p /opt/aflnet; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h \
      /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    git -C /opt/aflnet apply --check /tmp/mongodb-adapter/aflnet-graphviz-bool.patch; \
    git -C /opt/aflnet apply /tmp/mongodb-adapter/aflnet-graphviz-bool.patch; \
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
    cc -O2 -Wall -Wextra -Werror /tmp/mongodb-adapter/mongo-target-hold.c \
      -o /opt/benchmark/mongo-target-hold; \
    grep -a -q MONGODB /opt/aflnet/afl-fuzz; \
    apt-mark manual libcgraph8; \
    DEBIAN_FRONTEND=noninteractive apt-get purge -y build-essential git libgraphviz-dev patch; \
    apt-get autoremove -y; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/aflnet.tar.gz /tmp/mongodb-adapter /tmp/mongo-parser-test; \
    ldd /opt/aflnet/afl-fuzz | tee /tmp/aflnet-runtime-libraries.txt; \
    if grep -q 'not found' /tmp/aflnet-runtime-libraries.txt; then cat /tmp/aflnet-runtime-libraries.txt; exit 1; fi; \
    rm /tmp/aflnet-runtime-libraries.txt

COPY . /opt/benchmark/
RUN set -eux; \
    chmod +x /opt/benchmark/*.sh; \
    /usr/bin/mongod --version | tee /opt/benchmark/mongod-version.txt; \
    /usr/bin/mongosh --version | tee /opt/benchmark/mongosh-version.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort \
      > /opt/benchmark/build-package-manifest.txt; \
    sha256sum /opt/aflnet/afl-fuzz /usr/bin/mongod \
      /opt/benchmark/mongodb_aflnet.c /opt/benchmark/mongo-target-hold \
      > /opt/benchmark/build-binaries.sha256; \
    chown -R 1000:1000 /opt/benchmark /opt/aflnet

USER 1000:1000
ENTRYPOINT []
CMD ["/opt/benchmark/run.sh", "/results/fuzz-30m", "30m"]
