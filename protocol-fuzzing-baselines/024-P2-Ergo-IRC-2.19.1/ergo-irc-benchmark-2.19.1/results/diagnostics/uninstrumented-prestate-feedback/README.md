# Superseded precheck: dumb mode without state-sequence queueing

This 13m57s precheck is not the formal Ergo result. AFLNet `-n` recorded only the five initial seeds (`paths_total=5`, `paths_found=0`, `bitmap_cvg=0.00%`) because upstream AFLNet used the empty code bitmap as its queue-admission signal. It is retained as diagnostic evidence for the state-feedback patch added to this package. The formal run uses a patched AFLNet that queues inputs on newly discovered IRC response-state sequences; code coverage remains measured separately through Go coverage replay.
