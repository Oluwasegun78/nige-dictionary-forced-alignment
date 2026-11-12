#!/bin/bash
# Extract formants from the extension alignments with the same new-fave version and the same configuration as the study set.
# Reads the recordings and TextGrids from the LOCAL MFA working folder (~/mfa_work_ext), not from OneDrive, whose reads time out.
# Usage: bash ~/fave_extension.sh                          (all four dictionaries)
#        DICTS="Indian UK US" bash ~/fave_extension.sh      (only these; the others' results are left alone)
# One run at a time: a second copy refuses to start.
VENV="${VENV:-$HOME/venvs/newfave}"
source "$VENV/bin/activate"
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
B="${B:-$OD/POMA_New_20261110}"
EXT="$B/extension"
WORK="${WORK:-$HOME/fave_work_ext}"
MFA_WORK="${MFA_WORK:-$HOME/mfa_work_ext}"
DICTS="${DICTS:-NigE Indian UK US}"
LOCK="$HOME/.fave_extension.lock"
mkdir "$LOCK" 2>/dev/null || { echo "Another run of this script is active, or one stopped without cleaning up. If none is running: rmdir $LOCK"; exit 1; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
trap 'echo "Interrupted."; exit 130' INT TERM
VER=$(pip show new-fave | awk '/^Version:/ {print $2}')
[ "$VER" = "1.2.1" ] || { echo "new-fave is version '$VER' in $VENV, not 1.2.1. Stop."; exit 1; }
rm -rf "$WORK"; mkdir -p "$WORK/in" "$WORK/out" "$WORK/logs" "$EXT/fave_runs/logs"
# The configuration is written here and never copied from OneDrive: a timed-out copy once left the file empty.
cat > "$WORK/ft-config.yml" <<'EOC'
target_labels: "^[aeiouɑɒæɐɘəɚɛɜɝɨɪɔɵøʉʊʌ]"
EOC
[ -s "$WORK/ft-config.yml" ] && grep -q '^target_labels:' "$WORK/ft-config.yml" || { echo "Configuration file is empty or wrong. Stop."; exit 1; }
cat "$WORK/ft-config.yml"
if cmp -s "$WORK/ft-config.yml" "$B/fave_runs/ft-config_used.yml" 2>/dev/null; then echo "Configuration identical to the study set's ft-config_used.yml."
else echo "NOTE: identity with the study set's ft-config_used.yml could not be confirmed here (OneDrive). Compare by hand:  cat \"$B/fave_runs/ft-config_used.yml\""; fi
echo "Version: $VER" | tee "$WORK/new-fave_version.txt"
put() { local src="$1" dst="$2" ok=0 t; for t in 1 2 3 4; do if cp "$src" "$dst" 2>/dev/null && cmp -s "$src" "$dst"; then ok=1; break; fi; rm -f "$dst"; sleep 3; done; [ "$ok" -eq 1 ] || echo "COPY FAILED: $dst"; }
put "$WORK/new-fave_version.txt" "$EXT/fave_runs/new-fave_version.txt"
put "$WORK/ft-config.yml" "$EXT/fave_runs/ft-config_used.yml"
for V in $DICTS; do
  echo "=== $V  $(date)"
  rm -rf "$EXT/fave_runs/$V"
  mkdir -p "$WORK/in/$V"
  if ls "$MFA_WORK/out/$V"/*.TextGrid >/dev/null 2>&1 && ls "$MFA_WORK/in/ext_$V"/*.wav >/dev/null 2>&1; then
    cp "$MFA_WORK/in/ext_$V"/*.wav "$MFA_WORK/out/$V"/*.TextGrid "$WORK/in/$V/" || { echo "COPY FAILED (local) $V"; continue; }
  else
    echo "   local MFA folder not found for $V; falling back to OneDrive (may time out)"
    cp "$EXT/$V"/*.wav "$EXT/$V"/*.TextGrid "$WORK/in/$V/" || { echo "COPY FAILED $V"; continue; }
  fi
  echo "   input: $(ls "$WORK/in/$V"/*.TextGrid | wc -l) TextGrids, $(ls "$WORK/in/$V"/*.wav | wc -l) wav"
  if (cd "$WORK" && fave-extract corpus "in/$V" --ft-config ft-config.yml --destination "out/$V" > "logs/$V.log" 2>&1); then echo "OK $V"; else echo "FAILED $V"; tail -n 8 "$WORK/logs/$V.log"; fi
  mkdir -p "$EXT/fave_runs/$V"
  for f in "$WORK/out/$V"/*; do [ -f "$f" ] && put "$f" "$EXT/fave_runs/$V/$(basename "$f")"; done
  put "$WORK/logs/$V.log" "$EXT/fave_runs/logs/$V.log"
  echo "$V: $(ls "$EXT/fave_runs/$V"/*tracks.csv 2>/dev/null | wc -l) tracks files in OneDrive; $(ls "$WORK/out/$V"/*tracks.csv 2>/dev/null | wc -l) extracted"
done
