#!/bin/bash
# Build the extension corpus: the 31 recordings that had no transcript (dem_09, dem_11, dem_14 are excluded by design).
# Put the 31 transcripts in $B/extension_transcripts/ as <name>.txt, then run:  bash ~/make_extension_corpus.sh
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
B="${B:-$OD/POMA_New_20261110}"
AUDIO_SRC="${AUDIO_SRC:-$B/extension_audio}"     # filled by copy_extension_sources.sh (audio and transcript from the same ICE_raw folder)
TXT_IN="${TXT_IN:-$B/extension_transcripts}"
EXT="$B/extension"
EXPECTED="unsp_11 unsp_02 unsp_03 unsp_13 nbtal_08 dem_06 unsp_45 dem_04 com_32 unsp_32 dem_03 com_01 bnew_02 nbtal_10 com_34 com_38 com_05 com_35 com_42 bnew_16 com_06 com_27 bnew_34 com_19 com_31 bnew_15 bnew_27 bnew_23 dem_02 unsp_01 unsp_04"
mkdir -p "$TXT_IN" "$EXT/NigE" "$EXT/Indian" "$EXT/UK" "$EXT/US"
REPORT="$EXT/extension_report.csv"; echo "file,channels,sample_rate_hz,seconds,status" > "$REPORT"
: > "$EXT/extension_files.txt"
ok=0; bad=0
for s in $EXPECTED; do
  a=$(find "$AUDIO_SRC" -maxdepth 1 -type f \( -iname "$s.wav" -o -iname "$s.mp3" \) ! -name '._*' | head -1)
  t="$TXT_IN/$s.txt"
  status="ok"; ch=NA; hz=NA; sec=NA
  if [ -z "$a" ]; then status="no audio found"
  elif [ ! -s "$t" ]; then status="no transcript yet"
  else
    case "$a" in
      *.wav|*.WAV) ;;
      *) status="not a wav file: convert with  afconvert -f WAVE -d LEI16 in.mp3 out.wav" ;;
    esac
    if [ "$status" = "ok" ]; then
      info=$(python3 - "$a" <<'EOP'
import sys, wave
try:
    w = wave.open(sys.argv[1]); print(w.getnchannels(), w.getframerate(), round(w.getnframes() / w.getframerate(), 1))
except Exception as e:
    print("ERR 0 0")
EOP
)
      set -- $info; ch=$1; hz=$2; sec=$3
      if [ "$ch" = "ERR" ]; then status="cannot read the audio (not PCM wav, or the file is online-only: open it once in Finder)"
      elif [ "$ch" != "1" ]; then status="not mono ($ch channels): convert first"; fi
    fi
  fi
  if [ "$status" = "ok" ]; then
    tmp=$(mktemp)
    if python3 - "$t" "$tmp" <<'EOP'
import sys
b = open(sys.argv[1], "rb").read()
if b[:3] == b"\xef\xbb\xbf": b = b[3:]
try:
    t = b.decode("utf-8")
except UnicodeDecodeError:
    sys.exit(1)
t = " ".join(t.replace("\r", "\n").split()) + "\n"
open(sys.argv[2], "w", encoding="utf-8").write(t)
EOP
    then
      for V in NigE Indian UK US; do cp "$a" "$EXT/$V/$s.wav"; cp "$tmp" "$EXT/$V/$s.txt"; done
      echo "$s" >> "$EXT/extension_files.txt"; ok=$((ok+1))
    else status="transcript is not UTF-8 text: save it as UTF-8"; fi
    rm -f "$tmp"
  fi
  [ "$status" = "ok" ] || { bad=$((bad+1)); echo "  $s: $status"; }
  echo "$s,$ch,$hz,$sec,$status" >> "$REPORT"
done
echo
echo "Ready: $ok of 31   Not ready: $bad   (details: $REPORT)"
for V in NigE Indian UK US; do echo "$V: $(ls "$EXT/$V"/*.txt 2>/dev/null | wc -l) txt, $(ls "$EXT/$V"/*.wav 2>/dev/null | wc -l) wav"; done
python3 - "$REPORT" <<'EOP'
import csv, sys
r = [x for x in csv.DictReader(open(sys.argv[1], encoding="utf-8")) if x["status"] == "ok"]
print(f"Hours ready: {sum(float(x['seconds']) for x in r)/3600:.2f}")
EOP
