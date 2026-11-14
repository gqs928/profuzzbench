FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG OPENSMTPD_VERSION=7.9.0p0
ARG OPENSMTPD_COMMIT=769f646787362a1a31b350a2521253221a01b0c7
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ENV AFL_PATH=/opt/aflnet AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
WORKDIR /work

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    autoconf automake bison build-essential ca-certificates coreutils graphviz libbsd-dev \
    gcovr libevent-dev libgraphviz-dev libssl-dev libtool pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/OpenSMTPD-769f646.tar.gz /tmp/OpenSMTPD-769f646.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY smtpd.conf aliases run.sh smoke.py validate.sh capture-build.sh /work/
COPY seeds/ /work/seeds/
COPY smtp.dict /work/smtp.dict
COPY opensmtpd-fuzz-helper.c /tmp/opensmtpd-fuzz-helper.c

RUN set -eux; cd /tmp; sha256sum -c SHA256SUMS; \
    mkdir -p /src/OpenSMTPD /opt/aflnet /opt/opensmtpd /work/build-evidence /work/results /work/mailboxes /var/empty /var/spool/smtpd /etc/mail; \
    tar -xzf /tmp/OpenSMTPD-769f646.tar.gz --strip-components=1 -C /src/OpenSMTPD; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c; \
    AFL_NO_X86=1 CFLAGS='-O3 -funroll-loops -Wall -D_GNU_SOURCE -include libgen.h -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign -Wno-unused-result -DTRUE=1 -DFALSE=0' \
      make -C /opt/aflnet -j2 afl-fuzz afl-gcc afl-showmap afl-as; \
    cd /src/OpenSMTPD; ./bootstrap; \
    CC=gcc CFLAGS='-O1 -g --coverage -fno-omit-frame-pointer -fprofile-abs-path' LDFLAGS='--coverage' \
      ./configure --prefix=/opt/opensmtpd --with-user-smtpd=_smtpd --with-user-queue=_smtpq \
      --with-group-queue=_smtpq --with-path-mbox=/work/mailboxes; \
    make -j2; make install; rm -f /src/OpenSMTPD/a-conftest.gcno /src/OpenSMTPD/a-conftest.gcda; \
    groupadd --system _smtpd; useradd --system --gid _smtpd --home-dir /var/empty --shell /usr/sbin/nologin _smtpd; \
    groupadd --system _smtpq; useradd --system --gid _smtpq --home-dir /var/empty --shell /usr/sbin/nologin _smtpq; \
    useradd --system --create-home --home-dir /work/mailhome --shell /usr/sbin/nologin fuzzmail; \
    chown root:root /var/spool/smtpd; chmod 0711 /var/spool/smtpd; \
    chown _smtpq:_smtpq /work/mailboxes; chmod 0555 /var/empty; \
    install -m 0644 /work/aliases /etc/mail/aliases; \
    printf 'target_version=%s\ntarget_commit=%s\n' "${OPENSMTPD_VERSION}" "${OPENSMTPD_COMMIT}" > /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\nbase_image=%s\n' "${AFLNET_COMMIT}" 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852' >> /work/build-evidence/build-lock.txt; \
    printf 'gcc=' >> /work/build-evidence/build-lock.txt; gcc --version | head -1 >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/afl-fuzz | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'target_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/opensmtpd/sbin/smtpd | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'coverage_tool=' >> /work/build-evidence/build-lock.txt; gcovr --version | head -1 >> /work/build-evidence/build-lock.txt; \
    printf 'coverage_compile_flags=%s\n' '--coverage -O1 -g -fno-omit-frame-pointer -fprofile-abs-path (GCOV counters, not AFL mutation feedback)' >> /work/build-evidence/build-lock.txt; \
    printf 'target_linkage:\n' >> /work/build-evidence/build-lock.txt; ldd /opt/opensmtpd/sbin/smtpd >> /work/build-evidence/build-lock.txt; \
    AFL_QUIET=1 AFL_PATH=/opt/aflnet /opt/aflnet/afl-gcc -O2 -g -Wall -Wextra -Werror /tmp/opensmtpd-fuzz-helper.c -o /opt/aflnet/opensmtpd-fuzz-helper; \
    printf 'helper_source_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /tmp/opensmtpd-fuzz-helper.c | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh

ENTRYPOINT ["/bin/bash"]
