#!/bin/bash
OD="${OD:-/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh}"
D="$OD/POMA_New_20261110/blind_sample_v2"
AUD="${AUD:-$HOME/annotation_audio}"
PK="$HOME/second_annotator_package"
[ -d "$PK" ] || { echo "Build the package first (make_annotator_package.sh)"; exit 1; }
cp "$D/reliability_glide_check.csv" "$PK/" || { echo "reliability_glide_check.csv not found"; exit 1; }
tail -n +2 "$PK/reliability_glide_check.csv" | cut -d, -f2 | sort -u | while read -r s; do
  [ -f "$PK/audio/$s.wav" ] || cp "$AUD/$s.wav" "$PK/audio/" 2>/dev/null || echo "audio missing: $s"
done
if ! grep -q "reliability_glide_check" "$PK/INSTRUCTIONS.txt"; then
cat >> "$PK/INSTRUCTIONS.txt" <<'EOT'

Second file
After reliability_second_annotator.csv, please also annotate reliability_glide_check.csv (about 24 rows) in the same way.
Use a separate output file, for example reliability_glide_check_annotated.tsv.
For this file, if you hear a glide (a vowel that changes quality within the vowel), choose the vowel you hear at its core and write the whole sound in the "Type if other" box, for example ou or ei, or write "glide" in the notes.
EOT
fi
(cd "$HOME" && rm -f second_annotator_package.zip && zip -qr second_annotator_package.zip second_annotator_package)
echo "Package updated: $(ls "$PK/audio" | wc -l) recordings, $(du -sh "$PK" | cut -f1). Zip: $HOME/second_annotator_package.zip"
