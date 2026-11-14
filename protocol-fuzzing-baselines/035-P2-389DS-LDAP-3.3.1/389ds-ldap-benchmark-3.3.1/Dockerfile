ARG DS_BASE=docker.io/library/fedora@sha256:a7d72ba2745b100a3351087472e5ee7b2450af7cf331e7673007e3817612839c
FROM ${DS_BASE}
ARG DS_RPM_VERSION=3.3.1-3.fc45
RUN dnf -y install "389-ds-base-${DS_RPM_VERSION}" \
    && dnf clean all \
    && rm -rf /var/cache/dnf \
    && test "$(rpm -q --qf '%{VERSION}-%{RELEASE}' 389-ds-base)" = "${DS_RPM_VERSION}" \
    && ns-slapd -v 2>&1 | grep -F '389-Directory/3.3.1'
COPY build/afl-fuzz /opt/benchmark/build/afl-fuzz
COPY build/ldap-ready-check /opt/benchmark/build/ldap-ready-check
COPY seeds/ /opt/benchmark/seeds/
COPY ldap.dict server.sh fuzz.sh container-start.sh instance.inf /opt/benchmark/
RUN chmod 0755 /opt/benchmark/fuzz.sh /opt/benchmark/server.sh \
    /opt/benchmark/container-start.sh /opt/benchmark/build/afl-fuzz \
    /opt/benchmark/build/ldap-ready-check
CMD ["/opt/benchmark/container-start.sh"]
EXPOSE 3389
