# Package manifest

The standalone delivery package contains the Postfix source archive and signature evidence, pinned AFLNet source, profile configuration, source/build locks, seeds, the 30-minute campaign, corrected raw/framed replay classifications, replay/post-smoke coverage, and shutdown evidence. It deliberately excludes the central automated-framework experience library and contains no individual experience entry.

Every packaged source archive is checked by SHA-256. The delivery ZIP is CRC-tested and accompanied by a SHA-256 sidecar. The package records candidate archive validation and exact image cleanup; no global Docker prune is performed.
