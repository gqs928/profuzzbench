FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
ENV DEBIAN_FRONTEND=noninteractive
COPY source/bootstrap-mozilla-ca-bundle.pem /tmp/bootstrap-mozilla-ca-bundle.pem
RUN sed -i 's@http://archive.ubuntu.com/ubuntu/@https://archive.ubuntu.com/ubuntu/@; s@http://security.ubuntu.com/ubuntu/@https://security.ubuntu.com/ubuntu/@; s@Suites: noble noble-updates noble-backports@Suites: noble noble-updates@; s@Components: main universe restricted multiverse@Components: main universe@; s@Components: main universe restricted$@Components: main universe@' /etc/apt/sources.list.d/ubuntu.sources && \
    apt-get -o Acquire::https::CaInfo=/tmp/bootstrap-mozilla-ca-bundle.pem -o Acquire::https::Verify-Peer=true -o Acquire::https::Verify-Host=true -o Acquire::Retries=1 update && \
    (apt-get -o Acquire::https::CaInfo=/tmp/bootstrap-mozilla-ca-bundle.pem -o Acquire::https::Verify-Peer=true -o Acquire::https::Verify-Host=true install -y --no-install-recommends \
      build-essential ca-certificates cmake pkg-config python3 openssh-client \
      libpcre2-dev libssh-dev libssl-dev libxml2-dev libcurl4-openssl-dev \
      libsystemd-dev zlib1g-dev || (apt-get -o Acquire::https::CaInfo=/tmp/bootstrap-mozilla-ca-bundle.pem -o Acquire::https::Verify-Peer=true -o Acquire::https::Verify-Host=true -o Acquire::Retries=1 update && \
        apt-get -o Acquire::https::CaInfo=/tmp/bootstrap-mozilla-ca-bundle.pem -o Acquire::https::Verify-Peer=true -o Acquire::https::Verify-Host=true install -y --no-install-recommends \
          build-essential ca-certificates cmake pkg-config python3 openssh-client \
          libpcre2-dev libssh-dev libssl-dev libxml2-dev libcurl4-openssl-dev \
          libsystemd-dev zlib1g-dev)) && \
    rm -rf /var/lib/apt/lists/* /tmp/bootstrap-mozilla-ca-bundle.pem
COPY source/libyang-v6.4.13.tar.gz /tmp/sources/libyang.tar.gz
COPY source/sysrepo-v5.2.27.tar.gz /tmp/sources/sysrepo.tar.gz
COPY source/libnetconf2-v4.6.4.tar.gz /tmp/sources/libnetconf2.tar.gz
COPY source/netopeer2-2.8.21.tar.gz /tmp/sources/netopeer2.tar.gz
COPY build/afl-fuzz /opt/aflnet/afl-fuzz
COPY netconf_aflnet.c netconf.dict protocol_smoke.py replay_queue.py netconf_proxy.py \
     container-start.sh server.sh server-recover.sh fuzz.sh /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
ARG LIBYANG_SHA256=bf78a437225027ce9e20d2c449b7853204d7fd450bb00fb01e83339145561a86
ARG SYSREPO_SHA256=f08ac11f5b3782ca1305974c4883b67f084f1acf73eadd346d94d2c428871bf1
ARG LIBNETCONF2_SHA256=0065711bb5a8794389e8da39681e1402474f729ef3a87b8052d0400484bfd29a
ARG NETOPEER2_SHA256=1ff5b2891443025b7c5fe8ddde109dc6531ec831079207a60b51906bc5690a0b
RUN set -eux; \
    cd /tmp/sources; \
    echo "$LIBYANG_SHA256  libyang.tar.gz" | sha256sum -c -; \
    echo "$SYSREPO_SHA256  sysrepo.tar.gz" | sha256sum -c -; \
    echo "$LIBNETCONF2_SHA256  libnetconf2.tar.gz" | sha256sum -c -; \
    echo "$NETOPEER2_SHA256  netopeer2.tar.gz" | sha256sum -c -; \
    mkdir -p /tmp/src /tmp/build; \
    tar -xzf libyang.tar.gz -C /tmp/src; \
    tar -xzf sysrepo.tar.gz -C /tmp/src; \
    tar -xzf libnetconf2.tar.gz -C /tmp/src; \
    tar -xzf netopeer2.tar.gz -C /tmp/src; \
    cmake -S /tmp/src/libyang-6.4.13 -B /tmp/build/libyang -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF; \
    cmake --build /tmp/build/libyang -j2; cmake --install /tmp/build/libyang; \
    cmake -S /tmp/src/sysrepo-5.2.27 -B /tmp/build/sysrepo -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DENABLE_EXAMPLES=OFF; \
    cmake --build /tmp/build/sysrepo -j2; cmake --install /tmp/build/sysrepo; \
    cmake -S /tmp/src/libnetconf2-4.6.4 -B /tmp/build/libnetconf2 -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DENABLE_SSH_TLS=ON; \
    cmake --build /tmp/build/libnetconf2 -j2; cmake --install /tmp/build/libnetconf2; \
    mkdir -p /root/.ssh /opt/benchmark/configs; chmod 700 /root/.ssh; \
    ssh-keygen -q -t ed25519 -N '' -C 'netopeer2-loopback-benchmark' -f /opt/benchmark/configs/client_key; \
    cp /opt/benchmark/configs/client_key.pub /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys; chmod 600 /opt/benchmark/configs/client_key; \
    cmake -S /tmp/src/netopeer2-2.8.21 -B /tmp/build/netopeer2 -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DBUILD_SERVER=ON -DBUILD_CLI=OFF -DENABLE_URL=OFF -DSYSREPO_SETUP=ON; \
    cmake --build /tmp/build/netopeer2 -j2; cmake --install /tmp/build/netopeer2; \
    ldconfig; \
    chmod 0755 /opt/aflnet/afl-fuzz /opt/benchmark/container-start.sh /opt/benchmark/server.sh /opt/benchmark/server-recover.sh /opt/benchmark/fuzz.sh /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py /opt/benchmark/netconf_proxy.py; \
    printf 'libyang=6.4.13\nsysrepo=5.2.27\nlibnetconf2=4.6.4\nnetopeer2=2.8.21\n' > /opt/benchmark/version-lock.txt; \
    rm -rf /tmp/sources /tmp/src /tmp/build
COPY netconf-ready-check.c /opt/benchmark/
RUN cc -O2 -Wall -Wextra -o /opt/benchmark/netconf-ready-check /opt/benchmark/netconf-ready-check.c && \
    chmod 0755 /opt/benchmark/netconf-ready-check
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 AFL_NO_X86=1
WORKDIR /opt/benchmark
EXPOSE 1830
CMD ["bash", "/opt/benchmark/container-start.sh"]
