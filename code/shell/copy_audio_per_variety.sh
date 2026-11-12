#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
SRC="$OD/ML_summer_classes/acoustical_POMA_submission"
DEST="$OD/POMA_New_20261110"

audio_source() {
  case "$1" in
    Indian)         echo "$SRC/combined_Indian/indian_annotate/corpus" ;;
    NigE)           echo "$SRC/combined_NigE/acoustic" ;;
    UK)             echo "$SRC/combined_UK/corpus" ;;
    US)             echo "$SRC/combined_US/annotate_US/corpus" ;;
    NigE_reference) echo "$SRC/combined_NigE_corrected/acoustic" ;;
  esac
}

for V in Indian NigE UK US NigE_reference; do
  S=$(audio_source "$V")
  if [ ! -d "$S" ]; then echo "$V: SOURCE FOLDER NOT FOUND: $S"; continue; fi
  copied=0; missing=0
  for t in "$DEST/$V"/*.txt; do
    stem=$(basename "${t%.txt}")
    a=$(find "$S" -type f \( -iname "$stem.wav" -o -iname "$stem.mp3" \) | head -1)
    if [ -n "$a" ]; then
      cp -f "$a" "$DEST/$V/" && copied=$((copied+1)) || echo "COPY FAILED: $a"
    else
      echo "$V: no audio for $stem in $S"; missing=$((missing+1))
    fi
  done
  echo "$V: copied $copied audio files, $missing missing   (source: $S)"
done

echo; echo "Comparison with the Indian copy (recordings should be identical):"
for V in NigE UK US NigE_reference; do
  diffc=0
  for a in "$DEST/Indian"/*.wav "$DEST/Indian"/*.mp3; do
    [ -e "$a" ] || continue
    b="$DEST/$V/$(basename "$a")"
    if [ -e "$b" ]; then cmp -s "$a" "$b" || { echo "  DIFFERS in $V: $(basename "$a")"; diffc=$((diffc+1)); }; fi
  done
  echo "$V: $diffc audio file(s) differ from the Indian copy"
done

echo; for V in Indian NigE UK US NigE_reference; do
  echo "$V: $(ls "$DEST/$V"/*.txt 2>/dev/null | wc -l) txt, $(ls "$DEST/$V"/*.wav "$DEST/$V"/*.mp3 2>/dev/null | wc -l) audio"
done
