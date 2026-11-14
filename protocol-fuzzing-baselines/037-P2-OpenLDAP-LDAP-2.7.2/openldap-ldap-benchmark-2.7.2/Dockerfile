FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
ENV DEBIAN_FRONTEND=noninteractive
COPY source/bootstrap-mozilla-ca-bundle.pem /tmp/bootstrap-mozilla-ca-bundle.pem
RUN sed -i 's@http://archive.ubuntu.com/ubuntu/@https://archive.ubuntu.com/ubuntu/@; s@http://security.ubuntu.com/ubuntu/@https://security.ubuntu.com/ubuntu/@; s@Suites: noble noble-updates noble-backports@Suites: noble noble-updates@; s@Components: main universe restricted multiverse@Components: main universe@; s@Components: main universe restricted$@Components: main universe@' /etc/apt/sources.list.d/ubuntu.sources && apt-get -o Acquire::https::CaInfo=/tmp/bootstrap-mozilla-ca-bundle.pem -o Acquire::https::Verify-Peer=true -o Acquire::https::Verify-Host=true -o Acquire::Retries=1 update && (apt-get -o Acquire::https::CaInfo=/tmp/bootstrap-mozilla-ca-bundle.pem -o Acquire::https::Verify-Peer=true -o Acquire::https::Verify-Host=true install -y --no-install-recommends build-essential ca-certificates libssl-dev libsasl2-dev libltdl-dev libsystemd-dev libargon2-dev zlib1g-dev libevent-dev passwd || (apt-get -o Acquire::https::CaInfo=/tmp/bootstrap-mozilla-ca-bundle.pem -o Acquire::https::Verify-Peer=true -o Acquire::https::Verify-Host=true -o Acquire::Retries=1 update && apt-get -o Acquire::https::CaInfo=/tmp/bootstrap-mozilla-ca-bundle.pem -o Acquire::https::Verify-Peer=true -o Acquire::https::Verify-Host=true install -y --no-install-recommends build-essential ca-certificates libsasl2-dev libltdl-dev libsystemd-dev libargon2-dev zlib1g-dev libevent-dev passwd libssl-dev)) && rm -rf /var/lib/apt/lists/* /tmp/bootstrap-mozilla-ca-bundle.pem
RUN apt-get -o Acquire::Retries=1 update && apt-get -o Acquire::Retries=1 install -y --no-install-recommends groff-base && rm -rf /var/lib/apt/lists/*
COPY source/openldap-2.7.2.tgz /tmp/openldap.tgz
ARG OPENLDAP_SHA256=aad731aa22118ff327b9b4ddfc4b6f18ef9476586205da88a532e90940b523d2
RUN echo "$OPENLDAP_SHA256  /tmp/openldap.tgz" | sha256sum -c - && mkdir -p /build && tar -xzf /tmp/openldap.tgz -C /build && cd /build/openldap-2.7.2 && ./configure --prefix=/opt/openldap --sysconfdir=/opt/openldap/etc --localstatedir=/var --enable-slapd --enable-modules --enable-dynamic --with-tls=openssl --with-cyrus-sasl --enable-mdb --enable-crypt --enable-spasswd && make depend && make -j2 && make install && useradd --system --no-create-home --shell /usr/sbin/nologin openldap && mkdir -p /var/lib/openldap-data /opt/benchmark/configs /opt/benchmark/build && ldconfig /opt/openldap/lib
COPY configs/slapd.conf /opt/benchmark/configs/slapd.conf
COPY configs/base.ldif /opt/benchmark/configs/base.ldif
COPY container-start.sh server.sh fuzz.sh ldap.dict /opt/benchmark/
COPY build/afl-fuzz /opt/benchmark/build/afl-fuzz
COPY build/ldap-ready-check /opt/benchmark/build/ldap-ready-check
COPY seeds/ /opt/benchmark/seeds/
RUN chmod 0755 /opt/benchmark/container-start.sh /opt/benchmark/server.sh /opt/benchmark/fuzz.sh /opt/benchmark/build/afl-fuzz /opt/benchmark/build/ldap-ready-check
EXPOSE 3389
ENTRYPOINT ["/opt/benchmark/container-start.sh"]
