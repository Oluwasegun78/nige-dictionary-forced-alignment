#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
CORP="$OD/POMA_New_20261110"
OUT="$CORP/audio_checks"
mkdir -p "$OUT"
command -v afinfo >/dev/null || { echo "afinfo not found (macOS only)"; exit 1; }

for V in Indian NigE UK US NigE_reference; do
  CSV="$OUT/${V}_audio_properties.csv"
  echo "variety,file_type,channels,sample_rate_hz,encoding,bit_depth,duration_sec,audio_bytes,bit_rate_bps,file" > "$CSV"
  for f in "$CORP/$V"/*.wav "$CORP/$V"/*.mp3 "$CORP/$V"/*.WAV "$CORP/$V"/*.MP3; do
    [ -e "$f" ] || continue
    info=$(afinfo "$f" 2>/dev/null)
    if [ -z "$info" ]; then echo "$V,NA,NA,NA,NA,NA,NA,NA,NA,\"$(basename "$f")\"" >> "$CSV"; continue; fi
    ftype=$(echo "$info" | grep -m1 "File type ID" | awk '{print $NF}')
    line=$(echo "$info" | grep -m1 "Data format")
    ch=$(echo "$line" | sed -E 's/.*Data format: *([0-9]+) ch.*/\1/')
    hz=$(echo "$line" | sed -E 's/.*ch, *([0-9]+) Hz.*/\1/')
    enc=$(echo "$line" | sed -E 's/.*Hz, *([^,]*).*/\1/' | tr -d ' ')
    bits=$(echo "$enc" | sed -nE 's/^(Int|Float)([0-9]+)$/\2/p'); [ -z "$bits" ] && bits="NA"
    dur=$(echo "$info" | grep -m1 "estimated duration" | awk '{print $3}')
    bytes=$(echo "$info" | grep -m1 "audio bytes" | awk '{print $3}')
    br=$(echo "$info" | grep -m1 "bit rate" | awk '{print $3}')
    echo "$V,${ftype:-NA},${ch:-NA},${hz:-NA},${enc:-NA},$bits,${dur:-NA},${bytes:-NA},${br:-NA},\"$(basename "$f")\"" >> "$CSV"
  done
  echo "$V: $(($(wc -l < "$CSV") - 1)) files written to $CSV"
done

echo; echo "=== Summary: number of files by sampling rate, channels and encoding (per variety)"
for V in Indian NigE UK US NigE_reference; do
  echo "--- $V"
  tail -n +2 "$OUT/${V}_audio_properties.csv" | awk -F, '{print $4" Hz | "$3" ch | "$5}' | sort | uniq -c | sort -rn
done

echo; echo "=== Differences between each variety and the Indian copy (same file name)"
DIFF="$OUT/audio_property_differences.csv"
echo "variety,file,sample_rate_hz,indian_sample_rate_hz,channels,indian_channels,audio_bytes,indian_audio_bytes" > "$DIFF"
for V in NigE UK US NigE_reference; do
  awk -F, 'NR==FNR { if (FNR>1) { r[$10]=$4; c[$10]=$3; b[$10]=$8 } next }
           FNR>1 { if (!($10 in r)) print $1","$10",NA,NA,NA,NA,NA,NA"; else if (r[$10]!=$4 || c[$10]!=$3 || b[$10]!=$8) print $1","$10","$4","r[$10]","$3","c[$10]","$8","b[$10] }' \
    "$OUT/Indian_audio_properties.csv" "$OUT/${V}_audio_properties.csv" >> "$DIFF"
done
echo "Rows in $DIFF (header excluded): $(($(wc -l < "$DIFF") - 1))"
echo "Results folder: $OUT"
