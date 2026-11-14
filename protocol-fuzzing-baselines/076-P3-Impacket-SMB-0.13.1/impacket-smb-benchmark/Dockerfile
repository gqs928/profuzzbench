ARG BASE_IMAGE=docker.io/library/python:3.13-slim@sha256:48d884813cf44e927cf64c5529dd630dd3b18338c6dc727991eef9b71e934a20
FROM ${BASE_IMAGE}
ARG IMPACKET_SHA256=ed91c802b6beff6546afd2262942bc1a188b4671fb91ec751d46a1d66d28c2cf
ARG ATHERIS_SHA256=f8a9f51ce8369026e8eb7b7174835e8c4c85a1a6db5d9add36c15100779d2a39
ARG SIX_SHA256=4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/opt/impacket-0.13.1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY source/impacket-0.13.1.tar.gz /tmp/impacket-0.13.1.tar.gz
COPY source/wheels/atheris-3.1.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl /tmp/wheels/atheris-3.1.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
COPY source/wheels/six-1.17.0-py2.py3-none-any.whl /tmp/wheels/six-1.17.0-py2.py3-none-any.whl
RUN echo "${IMPACKET_SHA256}  /tmp/impacket-0.13.1.tar.gz" | sha256sum -c - \
    && echo "${ATHERIS_SHA256}  /tmp/wheels/atheris-3.1.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl" | sha256sum -c - \
    && echo "${SIX_SHA256}  /tmp/wheels/six-1.17.0-py2.py3-none-any.whl" | sha256sum -c - \
    && mkdir -p /opt \
    && tar -xzf /tmp/impacket-0.13.1.tar.gz -C /opt \
    && rm /tmp/impacket-0.13.1.tar.gz \
    && python3 -m venv /opt/venv \
    && pip install --no-index --no-deps /tmp/wheels/atheris-3.1.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl /tmp/wheels/six-1.17.0-py2.py3-none-any.whl \
    && rm -rf /tmp/wheels

WORKDIR /opt/benchmark
COPY fuzz_smb.py generate_seeds.py summarize_fuzz_log.py run-container.sh /opt/benchmark/
RUN chmod 755 /opt/benchmark/run-container.sh \
    && mkdir -p /opt/benchmark/seeds /opt/benchmark/build-logs \
    && /opt/venv/bin/python /opt/benchmark/generate_seeds.py \
    && python --version > /opt/benchmark/build-logs/python-version.txt \
    && python -m pip freeze > /opt/benchmark/build-logs/python-packages.txt \
    && python -c 'import atheris; from impacket import smb3structs; print("Atheris", atheris.__version__ if hasattr(atheris, "__version__") else "3.1.0"); print("Impacket SMB2/3 structures", smb3structs.SMB2Packet.__module__)'

CMD ["/bin/bash"]
