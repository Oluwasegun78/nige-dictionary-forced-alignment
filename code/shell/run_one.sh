#!/bin/bash
export PATH="/opt/miniconda3/envs/aligner/bin:$PATH"
V="$1"; D="$2"
PM="$HOME/Documents/MFA/pretrained_models"
W="$HOME/mfa_work_aligner"; mkdir -p "$W/in" "$W/out"
rm -rf "$W/in/$V" "$W/out/$V"
cp -R "$HOME/poma_corpus/$V" "$W/in/$V" || { echo "copy failed"; exit 1; }
echo "$V: $(ls $W/in/$V/*.wav | wc -l) wav, $(ls $W/in/$V/*.txt | wc -l) txt"
mfa align --clean "$W/in/$V" "$PM/dictionary/$D.dict" "$PM/acoustic/english_mfa.zip" "$W/out/$V" > "$W/$V.log" 2>&1 \
  && echo "OK $V: $(find $W/out/$V -name '*.TextGrid' | wc -l) TextGrids" || { echo "FAILED $V"; tail -n 8 "$W/$V.log"; }
