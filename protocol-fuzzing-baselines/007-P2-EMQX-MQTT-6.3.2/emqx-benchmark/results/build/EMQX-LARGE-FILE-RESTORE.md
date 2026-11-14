# Restore the large EMQX build artifact

Original path: emqx-benchmark/results/build/emqx-6.3.2-ubuntu24.04-amd64.tar.gz
Original size: 118557093 bytes
Original SHA-256: ac3cdf7533e8576e4d92419412b206fa7adae791a8066a62f58e07627f06c2bb

The file exceeded GitHub's regular Git file-size limit, so its exact bytes are split into two adjacent files:

- emqx-6.3.2-ubuntu24.04-amd64.tar.gz.part-001
- emqx-6.3.2-ubuntu24.04-amd64.tar.gz.part-002

After downloading both part files, restore and verify it with:

    cat emqx-6.3.2-ubuntu24.04-amd64.tar.gz.part-001 emqx-6.3.2-ubuntu24.04-amd64.tar.gz.part-002 > emqx-6.3.2-ubuntu24.04-amd64.tar.gz
    echo 'ac3cdf7533e8576e4d92419412b206fa7adae791a8066a62f58e07627f06c2bb  emqx-6.3.2-ubuntu24.04-amd64.tar.gz' | sha256sum -c -

