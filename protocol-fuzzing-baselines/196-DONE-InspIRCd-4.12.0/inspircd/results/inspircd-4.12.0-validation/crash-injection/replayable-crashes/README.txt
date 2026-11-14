Command line used to find this crash:

/home/ubuntu/aflnet/afl-fuzz -i /tmp/inspircd-crash-injection-yrkrtay8/seed -x /home/ubuntu/experiments/irc.dict -o /results/crash-injection -N tcp://127.0.0.1/6667 -P IRC -E -q 3 -s 3 -R -K -D 100000 -W 100 -w 100000 -m none -t 5000+ -c /workspace/clean.sh /home/ubuntu/experiments/inspircd-afl/run/bin/inspircd -F -L -P -c /home/ubuntu/experiments/inspircd-afl/run/conf/inspircd.conf

If you can't reproduce a bug outside of afl-fuzz, be sure to set the same
memory limit. The limit used for this fuzzing session was 0 B.

Need a tool to minimize test cases before investigating the crashes or sending
them to a vendor? Check out the afl-tmin that comes with the fuzzer!

Found any cool bugs in open-source tools using afl-fuzz? If yes, please drop
me a mail at <lcamtuf@coredump.cx> once the issues are fixed - I'd love to
add your finds to the gallery at:

  http://lcamtuf.coredump.cx/afl/

Thanks :-)
