FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ENV DEBIAN_FRONTEND=noninteractive \
    AFL_PATH=/opt/aflnet \
    AFL_NO_UI=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1
WORKDIR /work

RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf automake bison build-essential ca-certificates coreutils \
    gcovr gnupg graphviz iproute2 libdb-dev libgraphviz-dev libicu-dev libnsl-dev libssl-dev libtool \
    pkg-config python3 python3-minimal zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/ /tmp/source/
COPY main.cf master.cf smtp.dict postfix-fuzz-helper.c \
     run-container.sh smoke.py replay.py generate_seeds.py \
     apply_aflnet_smtp_patch.py /work/
COPY seeds/ /work/seeds/

RUN set -eux; \
    cd /tmp/source; sha256sum -c SHA256SUMS; \
    mkdir -m 700 /tmp/postfix-gnupg; \
    gpg --homedir /tmp/postfix-gnupg --import wietse-venema-public-key.asc; \
    gpg --homedir /tmp/postfix-gnupg --verify postfix-3.11.7.tar.gz.gpg2 postfix-3.11.7.tar.gz \
      > /work/source-signature-verification.txt 2>&1; \
    cat /work/source-signature-verification.txt; \
    mkdir -p /src/postfix /opt/aflnet /opt/postfix /work/build-evidence /work/results; \
    tar -xzf postfix-3.11.7.tar.gz --strip-components=1 -C /src/postfix; \
    tar -xzf aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c; \
    python3 /work/apply_aflnet_smtp_patch.py /opt/aflnet /work/build-evidence; \
    AFL_NO_X86=1 CFLAGS='-O3 -funroll-loops -Wall -D_GNU_SOURCE -include libgen.h -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign -Wno-unused-result -DTRUE=1 -DFALSE=0' \
      make -C /opt/aflnet -j2 afl-fuzz afl-showmap afl-gcc afl-as; \
    cd /src/postfix; \
    make makefiles CC=gcc; \
    make -j2 DEBUG='-g --coverage -fprofile-abs-path -fno-omit-frame-pointer' OPT='-O1'; \
    groupadd --system postfix; groupadd --system postdrop; \
    useradd --system --gid postfix --home-dir /var/lib/postfix --shell /usr/sbin/nologin postfix; \
    mkdir -p /var/lib/postfix; \
    export command_directory=/usr/sbin daemon_directory=/usr/libexec/postfix \
      data_directory=/var/lib/postfix queue_directory=/var/spool/postfix \
      config_directory=/etc/postfix meta_directory=/etc/postfix \
      shlib_directory=/usr/lib/postfix mail_owner=postfix setgid_group=postdrop \
      sendmail_path=/usr/sbin/sendmail.postfix newaliases_path=/usr/bin/newaliases.postfix \
      mailq_path=/usr/bin/mailq.postfix manpage_directory=/usr/share/man \
      readme_directory=no html_directory=no; \
    make POSTFIX_INSTALL_OPTS=-non-interactive install; \
    chown postfix:postfix /var/lib/postfix; \
    cp /work/main.cf /etc/postfix/main.cf; \
    cp /work/master.cf /etc/postfix/master.cf; \
    chmod 0644 /etc/postfix/main.cf /etc/postfix/master.cf; \
    AFL_QUIET=1 AFL_PATH=/opt/aflnet /opt/aflnet/afl-gcc -O2 -g -Wall -Wextra -Werror \
      /work/postfix-fuzz-helper.c -o /opt/aflnet/postfix-fuzz-helper; \
    printf 'target_version=' > /work/build-evidence/build-lock.txt; \
    /usr/sbin/postconf -h mail_version >> /work/build-evidence/build-lock.txt; \
    printf 'source_sha256=' >> /work/build-evidence/build-lock.txt; \
    sha256sum /tmp/source/postfix-3.11.7.tar.gz | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'gpg_signing_key_fingerprint=%s\n' '622C7C012254C186677469C50C0B590E80CA15A7' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\n' '0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_smtp_patch_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /work/build-evidence/aflnet-smtp-data.patch | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_patched_aflnet_c_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/aflnet.c | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_patched_afl_fuzz_c_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/afl-fuzz.c | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'base_image=%s\n' 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852' >> /work/build-evidence/build-lock.txt; \
    printf 'gcc=' >> /work/build-evidence/build-lock.txt; gcc --version | head -1 >> /work/build-evidence/build-lock.txt; \
    printf 'gcovr=' >> /work/build-evidence/build-lock.txt; gcovr --version | head -1 >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/afl-fuzz | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'smtpd_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /usr/libexec/postfix/smtpd | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'master_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /usr/libexec/postfix/master | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    ldd /usr/libexec/postfix/smtpd > /work/build-evidence/smtpd-ldd.txt; \
    ldd /opt/aflnet/afl-fuzz > /work/build-evidence/aflnet-ldd.txt; \
    /usr/sbin/postconf -n > /work/build-evidence/postconf-effective.txt; \
    /usr/sbin/postconf -d import_environment > /work/build-evidence/import-environment-default.txt; \
    chmod 0755 /work/run-container.sh; \
    rm -rf /tmp/postfix-gnupg /tmp/source

CMD ["/work/run-container.sh"]
