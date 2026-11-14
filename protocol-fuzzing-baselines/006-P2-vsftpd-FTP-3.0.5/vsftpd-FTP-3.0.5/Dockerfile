FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_JOBS=1
ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential ca-certificates clang gcc gcovr graphviz-dev libcap2-dev libpam0g-dev \
      libssl-dev llvm llvm-dev make python3 \
    && rm -rf /var/lib/apt/lists/*

COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY source/vsftpd-3.0.5.tar.gz /tmp/vsftpd.tar.gz
COPY source/vsftpd-fuzz-lifecycle.patch /tmp/vsftpd-fuzz-lifecycle.patch
COPY source-checksums.sha256 /tmp/source-checksums.sha256

RUN cd /tmp \
    && sha256sum -c source-checksums.sha256 \
    && mkdir -p /opt/aflnet /src /opt/vsftpd-reference/sbin /opt/vsftpd-afl/sbin /opt/vsftpd-gcov/sbin \
    && ln -sf /usr/lib/x86_64-linux-gnu/libcap.so /usr/lib/libcap.so \
    && tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet \
    && tar -xzf /tmp/vsftpd.tar.gz -C /src \
    && make -C /opt/aflnet -j${MAKE_JOBS} all

RUN /opt/aflnet/afl-fuzz -h >/tmp/aflnet-help.txt 2>&1 || test "$?" -eq 1

RUN cd /src/vsftpd-3.0.5 \
    && make clean \
    && make -j${MAKE_JOBS} CFLAGS='-O1 -g -fno-omit-frame-pointer -fPIE -fstack-protector-strong -D_FORTIFY_SOURCE=2' \
           LINK='' LDFLAGS='-fPIE -pie -Wl,-z,relro -Wl,-z,now' \
    && cp vsftpd /opt/vsftpd-reference/sbin/vsftpd \
    && patch --dry-run -p1 < /tmp/vsftpd-fuzz-lifecycle.patch \
    && patch -p1 < /tmp/vsftpd-fuzz-lifecycle.patch \
    && make clean \
    && AFL_DONT_OPTIMIZE=1 AFL_USE_ASAN=1 make -j${MAKE_JOBS} CC=/opt/aflnet/afl-gcc \
           CFLAGS='-O1 -g -fno-omit-frame-pointer -fPIE -fstack-protector-strong -D_FORTIFY_SOURCE=2 -DVSFTP_FUZZ_SINGLE_CLIENT -DVSFTP_AFLNET_KEEPALIVE -DVSFTP_AS_LIMIT=0xffffffffffffffffUL' \
           LINK='' \
           LDFLAGS='-fPIE -pie -Wl,-z,relro -Wl,-z,now' \
    && cp vsftpd /opt/vsftpd-afl/sbin/vsftpd \
    && make clean \
    && make -j${MAKE_JOBS} CFLAGS='-O0 -g --coverage -fPIE -DVSFTP_FUZZ_SINGLE_CLIENT -DVSFTP_GCOV_TARGET' \
           LINK='' \
           LDFLAGS='--coverage -fPIE -pie' \
    && cp vsftpd /opt/vsftpd-gcov/sbin/vsftpd \
    && /opt/vsftpd-reference/sbin/vsftpd -v \
    && /opt/vsftpd-afl/sbin/vsftpd -v \
    && /opt/vsftpd-gcov/sbin/vsftpd -v

RUN useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin fuzz \
    && useradd --system --uid 10002 --home-dir /srv/ftp --shell /usr/sbin/nologin ftp \
    && mkdir -p /work/results /work/coverage-data /srv/ftp /usr/share/empty \
    && chmod 0555 /srv/ftp /usr/share/empty \
    && chown -R fuzz:fuzz /work /opt/aflnet \
    && chmod 0755 /opt/vsftpd-reference/sbin/vsftpd /opt/vsftpd-afl/sbin/vsftpd /opt/vsftpd-gcov/sbin/vsftpd

COPY vsftpd.conf /work/vsftpd.conf
COPY validate.py validate.sh run.sh postprocess.sh replay_corpus.py /work/
COPY seeds/generate_seeds.py /work/generate_seeds.py
COPY dictionary/ftp.dict /work/ftp.dict
RUN python3 /work/generate_seeds.py /work/seeds \
    && chown -R fuzz:fuzz /work /src/vsftpd-3.0.5 \
    && chmod +x /work/validate.sh /work/run.sh /work/postprocess.sh \
    && chmod 0777 /work/results /work/coverage-data

WORKDIR /work
USER fuzz
ENTRYPOINT ["/bin/bash"]
