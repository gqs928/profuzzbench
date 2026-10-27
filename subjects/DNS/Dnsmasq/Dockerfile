FROM ubuntu:20.04

# Install common dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && \
    apt-get -y install sudo \ 
    apt-utils \
    build-essential \
    openssl \
    clang \
    graphviz-dev \
    git \
    autoconf \
    libgnutls28-dev \
    libssl-dev \
    llvm \
    python3-pip \
    nano \
    net-tools \
    vim \
    gdb \
    netcat \
    strace \
    wget

# Add a new user ubuntu, pass: ubuntu
RUN groupadd ubuntu && \
    useradd -rm -d /home/ubuntu -s /bin/bash -g ubuntu -G sudo -u 1000 ubuntu -p "$(openssl passwd -1 ubuntu)"

RUN chmod 777 /tmp

RUN pip3 install gcovr==4.2

# Use ubuntu as default username
USER ubuntu
WORKDIR /home/ubuntu

# Import environment variable to pass as parameter to make (e.g., to make parallel builds with -j)
ARG MAKE_OPT

# Set up fuzzers
RUN git clone https://github.com/profuzzbench/aflnet.git && \
    cd aflnet && \
    make clean all $MAKE_OPT && \
    cd llvm_mode && make $MAKE_OPT

RUN git clone https://github.com/profuzzbench/aflnwe.git && \
    cd aflnwe && \
    make clean all $MAKE_OPT && \
    cd llvm_mode && make $MAKE_OPT

# Set up environment variables for AFLNet
ENV WORKDIR="/home/ubuntu/experiments"
ENV AFLNET="/home/ubuntu/aflnet"
ENV PATH="${PATH}:${AFLNET}:/home/ubuntu/.local/bin:${WORKDIR}"
ENV AFL_PATH="${AFLNET}"
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1


RUN mkdir $WORKDIR

USER root
RUN apt-get -y install dnsutils

COPY --chown=ubuntu:ubuntu dnsmasq.patch ${WORKDIR}/dnsmasq.patch

# Set up environment variables for ASAN
env ASAN_OPTIONS='abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1:detect_container_overflow=0:poison_array_cookie=0:malloc_fill_byte=0:max_malloc_fill_size=16777216'

# Download and compile Dnsmasq for fuzzing
RUN cd $WORKDIR && \
    wget -q https://thekelleys.org.uk/dnsmasq/dnsmasq-2.93.tar.gz -O dnsmasq-2.93.tar.gz && \
    echo "cc967771abdafeb43d10db18932d6b59fd4bed2c69c22acf8cb96aff6920d55f  dnsmasq-2.93.tar.gz" | sha256sum -c - && \
    mkdir dnsmasq && tar -xzf dnsmasq-2.93.tar.gz --strip-components=1 -C dnsmasq && \
    cd dnsmasq && \
    patch -p1 < ${WORKDIR}/dnsmasq.patch && \
    AFL_USE_ASAN=1 make CC=afl-clang-fast CFLAGS="-g -O1" $MAKE_OPT

# Download and compile Dnsmasq for coverage analysis
RUN cd $WORKDIR && \
    mkdir dnsmasq-gcov && tar -xzf dnsmasq-2.93.tar.gz --strip-components=1 -C dnsmasq-gcov && \
    cd dnsmasq-gcov && \
    patch -p1 < ${WORKDIR}/dnsmasq.patch && \
    make CC=gcc CFLAGS="-g -O0 -fprofile-arcs -ftest-coverage" LDFLAGS="--coverage" $MAKE_OPT


COPY --chown=ubuntu:ubuntu in-dns ${WORKDIR}/in-dns
COPY --chown=ubuntu:ubuntu dns.dict ${WORKDIR}/dns.dict
COPY --chown=ubuntu:ubuntu cov_script.sh ${WORKDIR}/cov_script
COPY --chown=ubuntu:ubuntu run.sh ${WORKDIR}/run
COPY --chown=ubuntu:ubuntu dnsmasq.conf ${WORKDIR}/dnsmasq.conf

RUN cp ${WORKDIR}/dnsmasq.conf /etc/ && \
    echo address=/test.com/5.5.5.5 | sudo tee -a /etc/dnsmasq.conf
