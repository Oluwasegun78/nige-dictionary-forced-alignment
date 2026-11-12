#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
DEST="$OD/POMA_New_20261110"
W="$HOME/mfa_work_aligner"
mkdir -p "$DEST/alignment_info"
for V in NigE Indian UK US; do
  n_src=$(ls "$W/out/$V"/*.TextGrid 2>/dev/null | wc -l)
  [ "$n_src" -gt 0 ] || { echo "$V: no TextGrids in $W/out/$V"; continue; }
  copied=0
  for f in "$W/out/$V"/*.TextGrid; do
    b=$(basename "$f"); ok=0
    for t in 1 2 3 4; do
      if cp "$f" "$DEST/$V/$b" 2>/dev/null && cmp -s "$f" "$DEST/$V/$b"; then ok=1; break; fi
      rm -f "$DEST/$V/$b"; sleep 3
    done
    if [ "$ok" -eq 1 ]; then rm "$f"; copied=$((copied+1)); else echo "FAILED, kept in place: $V/$b"; fi
  done
  [ -f "$W/out/$V/alignment_analysis.csv" ] && cp "$W/out/$V/alignment_analysis.csv" "$DEST/alignment_info/${V}_alignment_analysis.csv"
  cp "$W/$V.log" "$W/$V.command.txt" "$DEST/alignment_info/" 2>/dev/null
  echo "$V: moved $copied of $n_src TextGrids. Folder now: $(ls "$DEST/$V"/*.TextGrid | wc -l) TextGrid, $(ls "$DEST/$V"/*.wav | wc -l) wav, $(ls "$DEST/$V"/*.txt | wc -l) txt"
done
cp "$W/mfa_version.txt" "$W/model_and_dictionary_checksums.txt" "$DEST/alignment_info/" 2>/dev/null
echo "alignment_info: $(ls "$DEST/alignment_info" | wc -l) files"
