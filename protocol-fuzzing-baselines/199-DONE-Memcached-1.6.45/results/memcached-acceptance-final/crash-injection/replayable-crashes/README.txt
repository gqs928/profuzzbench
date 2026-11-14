Command line used to find this crash:

/home/ubuntu/aflnet/afl-fuzz -i /tmp/memcached-fault-seed -o /results/crash-injection -N tcp://127.0.0.1/11213 -P MEMCACHED -E -q 3 -s 3 -R -K -D 10000 -W 100 -w 100000 -m none -t 5000+ /home/ubuntu/experiments/memcached-fuzz/memcached -B ascii -p 11213 -U 0 -t 1

If you can't reproduce a bug outside of afl-fuzz, be sure to set the same
memory limit. The limit used for this fuzzing session was 0 B.

Need a tool to minimize test cases before investigating the crashes or sending
them to a vendor? Check out the afl-tmin that comes with the fuzzer!

Found any cool bugs in open-source tools using afl-fuzz? If yes, please drop
me a mail at <lcamtuf@coredump.cx> once the issues are fixed - I'd love to
add your finds to the gallery at:

  http://lcamtuf.coredump.cx/afl/

Thanks :-)
