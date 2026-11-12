#!/bin/bash
source ~/venvs/newfave/bin/activate
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
DEST="$OD/POMA_New_20261110"
mkdir -p "$HOME/fave_work" "$DEST/fave_runs/logs"
cat > "$HOME/fave_work/ft-config.yml" <<'EOC'
target_labels: "^[aeiouɑɒæɐɘəɚɛɜɝɨɪɔɵøʉʊʌ]"
EOC
cat "$HOME/fave_work/ft-config.yml"
pip show new-fave | grep Version | tee "$DEST/fave_runs/new-fave_version.txt"
cp "$HOME/fave_work/ft-config.yml" "$DEST/fave_runs/ft-config_used.yml"
for V in NigE Indian UK US; do
  echo "=== $V  $(date)"
  if (cd "$HOME/fave_work" && fave-extract corpus "$DEST/$V" --ft-config ft-config.yml --destination "$DEST/fave_runs/$V" > "$DEST/fave_runs/logs/$V.log" 2>&1); then echo "OK $V"; else echo "FAILED $V"; tail -n 8 "$DEST/fave_runs/logs/$V.log"; fi
  echo "$V: $(ls "$DEST/fave_runs/$V"/*tracks.csv 2>/dev/null | wc -l) tracks files"
done
