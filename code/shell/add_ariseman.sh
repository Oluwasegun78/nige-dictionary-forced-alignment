#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
SRC="$OD/Akinola_database/Ariseman_MFA"
DEST="$OD/POMA_New_20261110"

if [ ! -d "$SRC" ]; then echo "SOURCE NOT FOUND: $SRC"; exit 1; fi
echo "Source: $SRC"
echo "Audio in source: $(find "$SRC" -type f \( -iname '*.wav' -o -iname '*.mp3' \) ! -name '._*' | wc -l)   txt in source: $(find "$SRC" -type f -iname '*.txt' ! -name '._*' | wc -l)"

# Names that would collide with files already in the folders
find "$SRC" -type f \( -iname '*.wav' -o -iname '*.mp3' -o -iname '*.txt' \) ! -name '._*' | while IFS= read -r f; do
  b=$(basename "$f")
  if [ -e "$DEST/Indian/$b" ] && ! cmp -s "$f" "$DEST/Indian/$b"; then echo "NAME COLLISION (different content, not copied): $b"; fi
done

for V in Indian NigE UK US NigE_reference; do
  mkdir -p "$DEST/$V"
  find "$SRC" -type f \( -iname '*.wav' -o -iname '*.mp3' -o -iname '*.txt' \) ! -name '._*' -print0 | while IFS= read -r -d '' f; do
    cp -n "$f" "$DEST/$V/" || echo "COPY FAILED: $f"
  done
  echo "$V: $(ls "$DEST/$V"/*.txt 2>/dev/null | wc -l) txt, $(ls "$DEST/$V"/*.wav "$DEST/$V"/*.mp3 2>/dev/null | wc -l) audio"
done

echo
echo "Transcripts without audio / audio without transcripts in $DEST/Indian:"
for t in "$DEST/Indian"/*.txt; do s=$(basename "${t%.txt}"); ls "$DEST/Indian/$s".wav "$DEST/Indian/$s".mp3 >/dev/null 2>&1 || echo "  txt without audio: $s"; done
for a in "$DEST/Indian"/*.wav "$DEST/Indian"/*.mp3; do [ -e "$a" ] || continue; s=$(basename "${a%.*}"); [ -e "$DEST/Indian/$s.txt" ] || echo "  audio without txt: $s"; done
