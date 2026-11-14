Command line used to find this crash:

/home/ubuntu/aflnet/afl-fuzz -i /results/fuzz/input-seeds -o /results/fuzz/aflnet -t 1000+ -m none -N tcp://127.0.0.1/12049 -P NFS -D 100000 -q 3 -s 3 -E -K -R -c /workspace/clean.sh /home/ubuntu/experiments/ganesha-afl/bin/ganesha.nfsd -F -f /workspace/ganesha.conf -p /tmp/ganesha.pid -L /results/fuzz/ganesha-critical.log -N NIV_CRIT

If you can't reproduce a bug outside of afl-fuzz, be sure to set the same
memory limit. The limit used for this fuzzing session was 0 B.

Need a tool to minimize test cases before investigating the crashes or sending
them to a vendor? Check out the afl-tmin that comes with the fuzzer!

Found any cool bugs in open-source tools using afl-fuzz? If yes, please drop
me a mail at <lcamtuf@coredump.cx> once the issues are fixed - I'd love to
add your finds to the gallery at:

  http://lcamtuf.coredump.cx/afl/

Thanks :-)
