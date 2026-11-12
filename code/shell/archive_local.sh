#!/bin/bash
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
SRC="$OD/ML_summer_classes/acoustical_POMA_submission"
ARCH="$HOME/POMA_archive_$(date +%Y%m%d)"
mkdir -p "$ARCH/mfa_dictionaries" "$ARCH/mfa_runs"
for try in 1 2 3; do
  rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='*.wav' --exclude='*.mp3' --exclude='.DS_Store' \
    "$SRC/" "$ARCH/acoustical_POMA_submission/" && break
  echo "rsync try $try failed, retrying"; sleep 10
done
for f in ~/Documents/MFA/pretrained_models/dictionary/*.dict; do
  [ -s "$f" ] || { echo "WARNING: source dictionary is EMPTY: $f"; continue; }
  cp "$f" "$ARCH/mfa_dictionaries/"
done
cp ~/Documents/MFA/command_history.yaml ~/Documents/MFA/global_config.yaml "$ARCH/"
for d in ~/Documents/MFA/*/; do
  n=$(basename "$d")
  if ls "$d"*.yaml >/dev/null 2>&1 || [ -d "${d}alignment" ]; then
    mkdir -p "$ARCH/mfa_runs/$n"
    cp "$d"*.yaml "$ARCH/mfa_runs/$n/" 2>/dev/null
    cp "${d}alignment/alignment_analysis.csv" "$ARCH/mfa_runs/$n/" 2>/dev/null
  fi
done
shasum "$ARCH"/mfa_dictionaries/*.dict > "$ARCH/dictionary_checksums.txt"
echo "--- check: TextGrids source vs archive"
for p in combined_NigE_corrected/acoustic combined_NigE/acoustic combined_Indian/indian_annotate/corpus combined_UK/corpus combined_US/annotate_US/corpus; do
  echo "$p  source: $(find "$SRC/$p" -name '*.TextGrid' | wc -l)  archive: $(find "$ARCH/acoustical_POMA_submission/$p" -name '*.TextGrid' | wc -l)"
done
echo "--- empty files in the archive (should be none):"; find "$ARCH" -type f -size 0
echo "--- dictionary sizes:"; wc -c "$ARCH"/mfa_dictionaries/*.dict
echo "Archive: $ARCH"; du -sh "$ARCH"
