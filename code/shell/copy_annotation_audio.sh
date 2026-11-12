#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
SRC="$OD/POMA_New_20261110/NigE"
CSV="$OD/POMA_New_20261110/blind_sample_v2/blind_sample_for_annotation.csv"
DST="$HOME/annotation_audio"
mkdir -p "$DST"
tail -n +2 "$CSV" | cut -d, -f2 | sort -u | while read -r s; do
  [ -s "$DST/$s.wav" ] && continue
  ok=0
  for t in 1 2 3 4; do
    if cp "$SRC/$s.wav" "$DST/$s.wav" 2>/dev/null; then ok=1; break; fi
    rm -f "$DST/$s.wav"; sleep 3
  done
  [ "$ok" -eq 1 ] || echo "FAILED: $s"
done
echo "Recordings copied: $(ls "$DST"/*.wav | wc -l)"
du -sh "$DST"
