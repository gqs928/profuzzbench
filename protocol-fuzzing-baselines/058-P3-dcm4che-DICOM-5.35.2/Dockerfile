ARG DCM4CHE_IMAGE
ARG AFL_BUILDER_IMAGE=docker.io/rockylinux/rockylinux:9.8@sha256:ed654c694190a670bb5c33f68995b862214fc96ffbdca95e07a8935ba0a3717d

FROM ${AFL_BUILDER_IMAGE} AS afl_builder
USER root
RUN dnf install -y gcc make patch tar gzip \
    && dnf clean all
COPY graphviz-2.44.0-26.el9.x86_64.rpm graphviz-devel-2.44.0-26.el9.x86_64.rpm \
     rocky-linux-9-build-repo.key /tmp/
COPY aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-network-noforkserver.patch aflnet-dicom.patch dicom_aflnet.inc \
     dicom-parser-test.c /tmp/dicom-adapter/
RUN set -eux; \
    rpm --import /tmp/rocky-linux-9-build-repo.key; \
    echo '31a674d1d3f543f7bd6d6da6694e3d267dbd1b04ca5e739ba0bdab6bc0411d97  /tmp/graphviz-2.44.0-26.el9.x86_64.rpm' | sha256sum -c -; \
    echo '1c48cd518a01e8fda8a20017424b35978de19761ecaf08a74f7a25582904b230  /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm' | sha256sum -c -; \
    rpm --checksig --verbose /tmp/graphviz-2.44.0-26.el9.x86_64.rpm; \
    rpm --checksig --verbose /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm; \
    rpm -Uvh --nodeps /tmp/graphviz-2.44.0-26.el9.x86_64.rpm; \
    rpm -Uvh --nodeps /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm; \
    ldconfig; \
    echo '251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d  /tmp/aflnet.tar.gz' | sha256sum -c -; \
    mkdir -p /opt/aflnet; tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/dicom-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/dicom-adapter/aflnet-network-noforkserver.patch; \
    patch --batch --dry-run -p1 -d /opt/aflnet -i /tmp/dicom-adapter/aflnet-dicom.patch; \
    patch --batch --forward -p1 -d /opt/aflnet -i /tmp/dicom-adapter/aflnet-dicom.patch; \
    cp /tmp/dicom-adapter/dicom_aflnet.inc /opt/aflnet/dicom_aflnet.inc; \
    AFL_NO_X86=1 make -C /opt/aflnet -j1 all afl-fuzz afl-replay aflnet-replay; \
    cc -std=c99 -O2 -Wall -Wextra -Werror /tmp/dicom-adapter/dicom-parser-test.c -o /tmp/dicom-parser-test; \
    /tmp/dicom-parser-test; \
    grep -a -q DICOM /opt/aflnet/afl-fuzz; \
    mkdir -p /tmp/graphviz-runtime-libs; \
    cp -a /usr/lib64/libcgraph.so.6* /usr/lib64/libcdt.so.5* /usr/lib64/libgvc.so.6* \
      /usr/lib64/libpathplan.so.4* /usr/lib64/libxdot.so.4* /usr/lib64/libltdl.so.7* \
      /tmp/graphviz-runtime-libs/; \
    ldd /opt/aflnet/afl-fuzz | tee /tmp/afl-fuzz-build-ldd.txt; \
    if grep -q 'not found' /tmp/afl-fuzz-build-ldd.txt; then exit 1; fi; \
    rm -rf /tmp/aflnet.tar.gz /tmp/dicom-adapter /tmp/graphviz-2.44.0-26.el9.x86_64.rpm \
      /tmp/graphviz-devel-2.44.0-26.el9.x86_64.rpm /tmp/rocky-linux-9-build-repo.key

ARG DCM4CHE_IMAGE
FROM ${DCM4CHE_IMAGE} AS runtime
USER root
ENV DCM4CHE_HOME=/opt/dcm4che DCM4CHE_EXPECTED_VERSION=5.35.2 \
    AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 AFL_NO_UI=1 DICOM_PORT=11112
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash python3 libexpat1 libltdl7 zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/lib/x86_64-linux-gnu
COPY dcm4che-5.35.2-bin.tar.gz /tmp/dcm4che-bin.tar.gz
RUN echo 'fbb9ec00858d61f6e9f0e05990d544a0a9a92f3ddacdc59cf66e188f9a0617a8  /tmp/dcm4che-bin.tar.gz' | sha256sum -c - \
    && tar -xzf /tmp/dcm4che-bin.tar.gz -C /opt \
    && mv /opt/dcm4che-5.35.2 /opt/dcm4che \
    && rm /tmp/dcm4che-bin.tar.gz
COPY --from=afl_builder /opt/aflnet/ /opt/aflnet/
COPY --from=afl_builder /tmp/graphviz-runtime-libs/ /usr/lib/x86_64-linux-gnu/
COPY --from=afl_builder /tmp/afl-fuzz-build-ldd.txt /tmp/afl-fuzz-build-ldd.txt
COPY README.md PACKAGE-MANIFEST.md ACCEPTANCE.md source-lock.json \
     aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
     aflnet-network-noforkserver.patch aflnet-dicom.patch dicom_aflnet.inc \
     dicom-parser-test.c prepare_seeds.py protocol_smoke.py dicom_probe.py replay_queue.py \
     deadline_wrapper.py start-storescp.sh stop-storescp.sh reset-storescp.sh \
     run.sh dicom.dict compose.yaml seeds-manifest.json /opt/benchmark/
COPY seeds/ /opt/benchmark/seeds/
RUN set -eux; \
    ldconfig; \
    ldd /opt/aflnet/afl-fuzz | tee /opt/benchmark/afl-fuzz-runtime-ldd.txt; \
    if grep -q 'not found' /opt/benchmark/afl-fuzz-runtime-ldd.txt; then exit 1; fi; \
    /opt/dcm4che/bin/storescp -V | tee /opt/benchmark/storescp-version.txt; \
    grep -Fq '5.35.2' /opt/benchmark/storescp-version.txt; \
    java -version 2>&1 | tee /opt/benchmark/java-version.txt; \
    python3 -m py_compile /opt/benchmark/prepare_seeds.py /opt/benchmark/protocol_smoke.py \
      /opt/benchmark/dicom_probe.py /opt/benchmark/replay_queue.py /opt/benchmark/deadline_wrapper.py; \
    chmod +x /opt/benchmark/*.sh /opt/benchmark/*.py /opt/dcm4che/bin/storescp; \
    rm -f /tmp/afl-fuzz-build-ldd.txt
WORKDIR /opt/benchmark
ENTRYPOINT []
