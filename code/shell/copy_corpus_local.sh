#!/bin/bash
SRC="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh/POMA_New_20261110"
DST="$HOME/poma_corpus"
mkdir -p "$DST/Indian"
fail=0
for f in "$SRC/Indian"/*; do
  [ -f "$f" ] || continue
  b=$(basename "$f")
  [ -e "$DST/Indian/$b" ] && [ "$(stat -f%z "$f")" = "$(stat -f%z "$DST/Indian/$b")" ] && continue
  ok=0
  for try in 1 2 3 4 5 6; do
    if cp "$f" "$DST/Indian/$b" 2>/dev/null; then ok=1; break; fi
    rm -f "$DST/Indian/$b"; sleep 5
  done
  [ "$ok" -eq 1 ] || { echo "FAILED after retries: $b"; fail=$((fail+1)); }
done
echo "Indian: $(ls "$DST/Indian"/*.txt 2>/dev/null | wc -l) txt, $(ls "$DST/Indian"/*.wav 2>/dev/null | wc -l) audio, $fail failed"
if [ "$fail" -eq 0 ]; then
  for V in NigE UK US NigE_reference; do rm -rf "$DST/$V"; cp -R "$DST/Indian" "$DST/$V"; done
  for V in Indian NigE UK US NigE_reference; do echo "$V: $(ls "$DST/$V"/*.txt | wc -l) txt, $(ls "$DST/$V"/*.wav | wc -l) audio"; done
else
  echo "Fix the failed files first (see below), then run this script again. It only copies what is missing."
fi
