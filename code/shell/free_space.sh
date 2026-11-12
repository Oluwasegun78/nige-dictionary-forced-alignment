#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
DEST="$OD/POMA_New_20261110"
ok=1
for V in NigE Indian UK US; do
  cloud=0
  for f in "$DEST/$V"/*.wav; do [ "$(du -k "$f" | cut -f1)" -eq 0 ] && cloud=$((cloud+1)); done
  diffs=$(diff -rq --exclude='*.TextGrid' "$HOME/poma_corpus/$V" "$DEST/$V" 2>&1 | wc -l)
  echo "$V: $cloud cloud-only wav, $diffs differences from the local copy, $(ls "$DEST/$V"/*.TextGrid | wc -l) TextGrids"
  if [ "$cloud" -ne 0 ] || [ "$diffs" -ne 0 ]; then ok=0; fi
done
echo "Space that can be freed:"
du -sh ~/poma_corpus ~/mfa_work_aligner/in ~/poma_aligned "$DEST/NigE_reference" 2>/dev/null
du -sh "$DEST/_not_in_study" 2>/dev/null
if [ "$1" = "delete" ] && [ "$ok" -eq 1 ]; then
  rm -rf ~/poma_corpus ~/mfa_work_aligner/in ~/poma_aligned "$DEST/NigE_reference"
  for V in NigE UK US NigE_reference; do rm -rf "$DEST/_not_in_study/$V"; done
  echo "Freed. One copy of the extra recordings is kept in $DEST/_not_in_study/Indian"
else
  echo "Dry run, or a check failed: nothing was deleted."
fi
