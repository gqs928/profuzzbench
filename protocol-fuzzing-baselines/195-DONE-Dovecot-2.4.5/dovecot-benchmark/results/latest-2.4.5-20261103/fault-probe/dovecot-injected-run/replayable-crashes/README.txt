Command line used to find this crash:

/home/ubuntu/aflnet/afl-fuzz -i /results/fault-probe/trigger-seeds -x /workspace/dovecot-fault.dict -o /results/fault-probe/dovecot-injected-run -N tcp://127.0.0.1/1143 -P IMAP -E -q 3 -s 3 -R -K -D 500000 -W 100 -w 100000 -m none -t 10000+ -c /usr/local/sbin/dovecot-clean-maildir /home/ubuntu/experiments/dovecot-afl/sbin/dovecot -F -c /results/fault-probe/dovecot-fault.conf

If you can't reproduce a bug outside of afl-fuzz, be sure to set the same
memory limit. The limit used for this fuzzing session was 0 B.

Need a tool to minimize test cases before investigating the crashes or sending
them to a vendor? Check out the afl-tmin that comes with the fuzzer!

Found any cool bugs in open-source tools using afl-fuzz? If yes, please drop
me a mail at <lcamtuf@coredump.cx> once the issues are fixed - I'd love to
add your finds to the gallery at:

  http://lcamtuf.coredump.cx/afl/

Thanks :-)
