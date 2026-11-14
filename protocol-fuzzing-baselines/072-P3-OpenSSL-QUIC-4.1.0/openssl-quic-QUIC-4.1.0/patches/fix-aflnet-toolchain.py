#!/usr/bin/env python3
"""Apply narrow compatibility fixes for AFLNet 2.56b on current toolchains."""
from __future__ import annotations
import sys
from pathlib import Path
makefile=Path(sys.argv[1])
root=makefile.parent
s=makefile.read_text(encoding='utf-8')
before='main() { __asm__("xorb %al, %al"); }'
after='int main(void) { __asm__("xorb %al, %al"); return 0; }'
if s.count(before) != 1:
    raise SystemExit(f'expected one legacy x86 probe in {makefile}, found {s.count(before)}')
makefile.write_text(s.replace(before, after), encoding='utf-8')
config=root/'config.h'
c=config.read_text(encoding='utf-8')
needle='#include "types.h"'
compat='''#include "types.h"

#ifndef AFLNET_BOOL_COMPAT
#define AFLNET_BOOL_COMPAT
# ifndef FALSE
#  define FALSE 0
# endif
# ifndef TRUE
#  define TRUE 1
# endif
#endif'''
if c.count(needle) != 1:
    raise SystemExit(f'expected one type include in {config}')
config.write_text(c.replace(needle, compat), encoding='utf-8')
