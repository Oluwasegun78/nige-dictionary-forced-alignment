#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
TXT_SRC="$OD/POMA_archive_20261110/acoustical_POMA_submission/combined_Indian"
AUDIO_SRC="$OD/ML_summer_classes/acoustical_POMA_submission/combined_Indian/indian_annotate/corpus"
DEST="$OD/POMA_New_20261110"
VARIETIES="Indian NigE UK US NigE_reference"
EXCLUDE="dem_09 dem_11 dem_14"

mkdir -p "$DEST"
TMP=$(mktemp -d)

# 1. Collect the transcripts. If a name occurs more than once, the newest copy wins.
find "$TXT_SRC" -type f -name '*.txt' ! -name '._*' -print0 | xargs -0 ls -t | while IFS= read -r f; do
  b=$(basename "$f")
  [ -e "$TMP/$b" ] || cp "$f" "$TMP/$b"
done
echo "Transcripts found: $(ls "$TMP"/*.txt | wc -l)"

# 2. Pair each transcript with its audio file (same name, .wav or .mp3)
PAIRS="$TMP/pairs.tsv"; : > "$PAIRS"
NOAUDIO="$TMP/no_audio.txt"; : > "$NOAUDIO"
for t in "$TMP"/*.txt; do
  b=$(basename "$t"); stem="${b%.txt}"
  skip=0
  for x in $EXCLUDE; do [ "$stem" = "$x" ] && skip=1; done
  [ "$skip" -eq 1 ] && continue
  a=$(find "$AUDIO_SRC" -type f \( -iname "$stem.wav" -o -iname "$stem.mp3" \) | head -1)
  if [ -n "$a" ]; then printf '%s\t%s\n' "$t" "$a" >> "$PAIRS"; else echo "$stem" >> "$NOAUDIO"; fi
done
echo "Transcript + audio pairs: $(wc -l < "$PAIRS")"
echo "Transcripts without audio: $(wc -l < "$NOAUDIO")"

# 3. Copy the same pairs into each variety folder (existing files are not overwritten)
for V in $VARIETIES; do
  mkdir -p "$DEST/$V"
  while IFS=$'\t' read -r t a; do
    cp -n "$t" "$DEST/$V/" || echo "COPY FAILED: $t"
    cp -n "$a" "$DEST/$V/" || echo "COPY FAILED: $a"
  done < "$PAIRS"
  echo "$V: $(ls "$DEST/$V"/*.txt 2>/dev/null | wc -l) txt, $(ls "$DEST/$V"/*.wav "$DEST/$V"/*.mp3 2>/dev/null | wc -l) audio"
done

# 4. Audio files that have no transcript
n=0
for a in "$AUDIO_SRC"/*.wav; do
  s=$(basename "${a%.wav}")
  [ -e "$TMP/$s.txt" ] || n=$((n+1))
done
echo "Audio files in the source without a transcript: $n"
echo "Output: $DEST"
