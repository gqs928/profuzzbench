#!/usr/bin/env python3
"""Configure AFLNet to emit IPSM DOT directly, without Graphviz libraries."""
import pathlib, sys
root=pathlib.Path(sys.argv[1])
makefile=root/'Makefile'; text=makefile.read_text()
if '-lgvc -lcgraph' not in text: raise SystemExit('expected Graphviz link flags were not found')
text=text.replace('-lgvc -lcgraph','',1)
line='afl-fuzz: afl-fuzz.c $(COMM_HDR) aflnet.o stomp_aflnet.o aflnet.h | test_x86'
if line not in text: raise SystemExit('expected afl-fuzz dependency line was not found')
text=text.replace(line,line.replace('stomp_aflnet.o','stomp_aflnet.o graphviz_stub.o'),1)
cmd='$(CC) $(CFLAGS) $@.c aflnet.o stomp_aflnet.o -o $@ $(LDFLAGS)'
if cmd not in text: raise SystemExit('expected afl-fuzz link command was not found')
text=text.replace(cmd,cmd.replace('stomp_aflnet.o','stomp_aflnet.o graphviz_stub.o'),1)
rule='stomp_aflnet.o: stomp_aflnet.c $(COMM_HDR) aflnet.h\n\t$(CC) $(CFLAGS) -c $< -o $@'
if rule not in text: raise SystemExit('expected parser object rule was not found')
text=text.replace(rule,rule+'\n\ngraphviz_stub.o: graphviz_stub.c graphviz_stub.h\n\t$(CC) $(CFLAGS) -c $< -o $@',1)
makefile.write_text(text)
source=root/'afl-fuzz.c'; text=source.read_text()
needle='#include <graphviz/gvc.h>'
if needle not in text: raise SystemExit('Graphviz include not found')
source.write_text(text.replace(needle,'#include "graphviz_stub.h"',1))
