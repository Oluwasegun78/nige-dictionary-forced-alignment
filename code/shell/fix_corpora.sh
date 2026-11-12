#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
CORP="$OD/POMA_New_20261110"
LIST="$CORP/study_files.txt"
VARS="Indian NigE UK US NigE_reference"

echo "--- state now"
echo "study_files.txt lines: $( [ -f "$LIST" ] && wc -l < "$LIST" || echo missing )"
for V in $VARS; do
  echo "$V: $(ls "$CORP/$V" 2>/dev/null | wc -l) files in the folder; $(ls "$CORP/_not_in_study/$V" 2>/dev/null | wc -l) in _not_in_study"
done

echo "--- restoring everything from _not_in_study"
for V in $VARS; do
  if [ -d "$CORP/_not_in_study/$V" ]; then mv "$CORP/_not_in_study/$V"/* "$CORP/$V"/ 2>/dev/null; fi
  echo "$V: $(ls "$CORP/$V"/*.txt 2>/dev/null | wc -l) txt, $(ls "$CORP/$V"/*.wav 2>/dev/null | wc -l) audio"
done

echo "--- rebuilding the study list from the reference TextGrids"
REF=""
for c in "$OD/ML_summer_classes/acoustical_POMA_submission/combined_NigE_corrected/acoustic" \
         "$OD/POMA_archive_20261110/acoustical_POMA_submission/combined_NigE_corrected/acoustic"; do
  if [ -d "$c" ] && [ "$(ls "$c"/*.TextGrid 2>/dev/null | wc -l)" -ge 90 ]; then REF="$c"; break; fi
done
[ -n "$REF" ] || { echo "No reference folder with at least 90 TextGrids found. Stop."; exit 1; }
echo "Reference folder: $REF"
ls "$REF"/*.TextGrid | xargs -n1 basename | sed 's/\.TextGrid$//' | sort > "$LIST"
echo "Study recordings: $(wc -l < "$LIST")"
[ "$(wc -l < "$LIST")" -ge 90 ] || { echo "List too short. Stop."; exit 1; }

echo "--- pruning to the study recordings"
for V in $VARS; do
  mkdir -p "$CORP/_not_in_study/$V"
  for f in "$CORP/$V"/*; do
    [ -f "$f" ] || continue
    b=$(basename "$f"); stem="${b%.*}"
    if ! grep -qx -- "$stem" "$LIST"; then mv "$f" "$CORP/_not_in_study/$V/"; fi
  done
  echo "$V: $(ls "$CORP/$V"/*.txt 2>/dev/null | wc -l) txt, $(ls "$CORP/$V"/*.wav 2>/dev/null | wc -l) audio"
done
