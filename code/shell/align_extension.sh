#!/bin/bash
# Align the extension corpus with the same MFA 3.3.8, the same acoustic model and the same four dictionaries as the study set.
# Usage: conda activate aligner; bash ~/align_extension.sh aligner
ENV_NAME="${1:-aligner}"
BIN="${MFA_BIN_DIR:-/opt/miniconda3/envs/$ENV_NAME/bin}"
export PATH="$BIN:$PATH"
MFA="$BIN/mfa"
[ -x "$MFA" ] || { echo "No mfa at $MFA. Check: ls /opt/miniconda3/envs"; exit 1; }
command -v fstcompile >/dev/null || { echo "fstcompile not found in $ENV_NAME. Stop."; exit 1; }
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
B="${B:-$OD/POMA_New_20261110}"
EXT="$B/extension"
WORK="${WORK:-$HOME/mfa_work_ext}"
PM="${PM:-$HOME/Documents/MFA/pretrained_models}"
MODEL="$PM/acoustic/english_mfa.zip"
n_txt=$(ls "$EXT/NigE"/*.txt 2>/dev/null | wc -l)
[ "$n_txt" -ge 1 ] || { echo "No transcripts in $EXT/NigE. Run make_extension_corpus.sh first. Stop."; exit 1; }
for V in NigE Indian UK US; do
  t=$(ls "$EXT/$V"/*.txt 2>/dev/null | wc -l); a=$(ls "$EXT/$V"/*.wav 2>/dev/null | wc -l)
  echo "$V: $t txt, $a audio"
  [ "$t" -eq "$n_txt" ] && [ "$a" -eq "$n_txt" ] || { echo "Corpus $V does not match NigE. Stop."; exit 1; }
done
rm -rf "$WORK"; mkdir -p "$WORK/in" "$WORK/out" "$EXT/alignment_info"
"$MFA" configure --disable_mp
"$MFA" version > "$WORK/mfa_version.txt" 2>&1; cat "$WORK/mfa_version.txt"
shasum "$MODEL" "$PM"/dictionary/english_{nigeria,india,uk,us}_mfa.dict > "$WORK/model_and_dictionary_checksums.txt"
for pair in "NigE:english_nigeria_mfa" "Indian:english_india_mfa" "UK:english_uk_mfa" "US:english_us_mfa"; do
  V="${pair%%:*}"; D="${pair#*:}"
  echo "=== $V ($D)  $(date)"
  # the input folder is named ext_<variety>: MFA keeps its working files in ~/Documents/MFA/<folder name> and --clean deletes them,
  # so the study set's run folders (NigE, Indian, UK, US) are left untouched
  IN="$WORK/in/ext_$V"
  mkdir -p "$IN"; cp "$EXT/$V"/*.wav "$EXT/$V"/*.txt "$IN/" || { echo "COPY FAILED $V"; continue; }
  echo "$MFA align --clean $IN $PM/dictionary/$D.dict $MODEL $WORK/out/$V" > "$WORK/$V.command.txt"
  if "$MFA" align --clean "$IN" "$PM/dictionary/$D.dict" "$MODEL" "$WORK/out/$V" > "$WORK/$V.log" 2>&1; then
    echo "OK     $V: $(find "$WORK/out/$V" -name '*.TextGrid' | wc -l) TextGrids"
  else
    echo "FAILED $V -- last lines of its log:"; tail -n 8 "$WORK/$V.log"
  fi
  # bring the results back, checking each file byte for byte
  copied=0
  for f in "$WORK/out/$V"/*.TextGrid; do
    [ -e "$f" ] || continue
    b=$(basename "$f"); ok=0
    for t in 1 2 3 4; do
      if cp "$f" "$EXT/$V/$b" 2>/dev/null && cmp -s "$f" "$EXT/$V/$b"; then ok=1; break; fi
      rm -f "$EXT/$V/$b"; sleep 3
    done
    [ "$ok" -eq 1 ] && copied=$((copied+1)) || echo "COPY FAILED: $V/$b"
  done
  [ -f "$WORK/out/$V/alignment_analysis.csv" ] && cp "$WORK/out/$V/alignment_analysis.csv" "$EXT/alignment_info/${V}_alignment_analysis.csv"
  cp "$WORK/$V.log" "$WORK/$V.command.txt" "$EXT/alignment_info/" 2>/dev/null
  echo "$V: $copied TextGrids copied back."
  for w in "$EXT/$V"/*.wav; do s=$(basename "${w%.wav}"); [ -e "$EXT/$V/$s.TextGrid" ] || echo "  not aligned under $V: $s"; done
done
cp "$WORK/mfa_version.txt" "$WORK/model_and_dictionary_checksums.txt" "$EXT/alignment_info/" 2>/dev/null
echo "Finished: $(date)   Results and logs: $EXT  and  $EXT/alignment_info"
