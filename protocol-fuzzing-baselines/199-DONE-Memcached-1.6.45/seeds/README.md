# Memcached ASCII/TCP seed corpus

Each `*.hex` file encodes the exact bytes of one seed. `prepare-seeds.py`
materializes them as binary files with CRLF line endings inside the container.

- `seed-business.hex`: `set bench` → `get bench` → `delete bench` → `get bench`.
- `seed-set-get.hex`: stores a five-byte value, then retrieves it.
- `seed-version.hex`, `seed-stats.hex`, `seed-delete.hex`, `seed-quit.hex`:
  basic protocol/state probes.

The corpus is specifically for Memcached ASCII over TCP. It is not suitable
for the binary protocol or UDP mode.
