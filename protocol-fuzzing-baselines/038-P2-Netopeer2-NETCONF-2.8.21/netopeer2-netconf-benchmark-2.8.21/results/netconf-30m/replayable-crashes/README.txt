Command line used to find this crash:

/opt/aflnet/afl-fuzz -d -n -i /opt/benchmark/seeds -x /opt/benchmark/netconf.dict -o /results/netconf-30m -N tcp://127.0.0.1/1830 -P NETCONF -E -q 3 -s 3 -R -K -c /opt/benchmark/server-recover.sh /results/netconf-30m -D 10000 -W 100 -w 200000 -m none -t 15000+ /opt/benchmark/netconf-ready-check

If you can't reproduce a bug outside of afl-fuzz, be sure to set the same
memory limit. The limit used for this fuzzing session was 0 B.

Need a tool to minimize test cases before investigating the crashes or sending
them to a vendor? Check out the afl-tmin that comes with the fuzzer!

Found any cool bugs in open-source tools using afl-fuzz? If yes, please drop
me a mail at <lcamtuf@coredump.cx> once the issues are fixed - I'd love to
add your finds to the gallery at:

  http://lcamtuf.coredump.cx/afl/

Thanks :-)
