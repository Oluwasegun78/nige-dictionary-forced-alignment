#!/bin/bash
ENV_NAME="${1:-aligner}"
export PATH="/opt/miniconda3/envs/$ENV_NAME/bin:$PATH"
MFA="/opt/miniconda3/envs/$ENV_NAME/bin/mfa"
command -v fstcompile >/dev/null || { echo "fstcompile not found in $ENV_NAME. Stop."; exit 1; }
[ -x "$MFA" ] || { echo "No mfa at $MFA. Check: ls /opt/miniconda3/envs"; exit 1; }
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
CORP="$OD/POMA_New_20261110"
WORK="$HOME/mfa_work_$ENV_NAME"
PM="$HOME/Documents/MFA/pretrained_models"
MODEL="$PM/acoustic/english_mfa.zip"
rm -rf "$WORK"; mkdir -p "$WORK/in" "$WORK/out"

n_txt=$(ls "$CORP/Indian"/*.txt | wc -l)
[ "$n_txt" -ge 90 ] || { echo "Only $n_txt transcripts found. Stop."; exit 1; }
for V in NigE Indian UK US; do
  t=$(ls "$CORP/$V"/*.txt 2>/dev/null | wc -l); a=$(ls "$CORP/$V"/*.wav 2>/dev/null | wc -l)
  echo "$V: $t txt, $a audio"
  [ "$t" -eq "$n_txt" ] && [ "$a" -eq "$n_txt" ] || { echo "Corpus $V does not match the Indian one. Stop."; exit 1; }
done

"$MFA" configure --disable_mp
"$MFA" version > "$WORK/mfa_version.txt" 2>&1; cat "$WORK/mfa_version.txt"
shasum "$MODEL" "$PM"/dictionary/english_{nigeria,india,uk,us}_mfa.dict > "$WORK/model_and_dictionary_checksums.txt"

for pair in "NigE:english_nigeria_mfa" "Indian:english_india_mfa" "UK:english_uk_mfa" "US:english_us_mfa"; do
  V="${pair%%:*}"; D="${pair#*:}"
  echo "=== $V ($D)  $(date)"
  cp -R "$CORP/$V" "$WORK/in/$V" || { echo "COPY FAILED $V"; continue; }
  echo "$MFA align --clean $WORK/in/$V $PM/dictionary/$D.dict $MODEL $WORK/out/$V" > "$WORK/$V.command.txt"
  if "$MFA" align --clean "$WORK/in/$V" "$PM/dictionary/$D.dict" "$MODEL" "$WORK/out/$V" > "$WORK/$V.log" 2>&1; then
    echo "OK     $V: $(find "$WORK/out/$V" -name '*.TextGrid' | wc -l) TextGrids"
  else
    echo "FAILED $V -- last lines of its log:"; tail -n 8 "$WORK/$V.log"
  fi
done

mkdir -p "$CORP/alignments_$ENV_NAME"
cp -R "$WORK/out/." "$CORP/alignments_$ENV_NAME/"
cp "$WORK"/*.txt "$WORK"/*.log "$CORP/alignments_$ENV_NAME/" 2>/dev/null
echo "Copied to: $CORP/alignments_$ENV_NAME   Finished: $(date)"
