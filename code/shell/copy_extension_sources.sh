#!/bin/bash
# Copy the audio and the transcript of each extension recording from the ICE_raw folders into staging folders, and audit the transcripts.
# dem_09, dem_11 and dem_14 are excluded by design. Usage: bash ~/copy_extension_sources.sh
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
B="${B:-$OD/POMA_New_20261110}"
ICE="${ICE:-$OD/Desktop/ICE_raw}"
COM="$ICE/data_preparation_for_annotation/commentaries"
BNEW="$ICE/personal_Nigerian_English_projects/folder_for_s_in_NigE/bnew_augment"
UNSP="$ICE/data_preparation_for_annotation/unscripted_annotated"
DEM="$ICE/data_preparation_for_annotation/demonstrations"
NBT="$ICE/data_preparation_for_annotation/non_broadcast_talks"
OLD="${OLD:-$OD/ML_summer_classes/acoustical_POMA_submission/combined_Indian/indian_annotate/corpus}"
TXT_OUT="$B/extension_transcripts"; AUD_OUT="$B/extension_audio"
EXPECTED="com_32 com_01 com_06 com_27 com_19 com_31 com_34 com_38 com_05 com_35 com_42 bnew_02 bnew_16 bnew_34 bnew_15 bnew_27 bnew_23 unsp_11 unsp_01 unsp_04 unsp_02 unsp_03 unsp_13 unsp_45 unsp_32 dem_04 dem_02 dem_06 dem_03 nbtal_10 nbtal_08"
mkdir -p "$TXT_OUT" "$AUD_OUT"
for d in "$COM" "$BNEW" "$UNSP" "$DEM" "$NBT"; do [ -d "$d" ] && echo "folder found:     $d" || echo "FOLDER NOT FOUND: $d"; done
home_for() { case "$1" in com_*) echo "$COM";; bnew_*) echo "$BNEW";; unsp_*) echo "$UNSP";; dem_*) echo "$DEM";; nbtal_*) echo "$NBT";; esac; }
copy_safe() { local src="$1" dst="$2" ok=0 t
  for t in 1 2 3 4; do if cp "$src" "$dst" 2>/dev/null && cmp -s "$src" "$dst"; then ok=1; break; fi; rm -f "$dst"; sleep 3; done
  [ "$ok" -eq 1 ]; }
REP="$B/extension_sources_report.csv"; echo "file,transcript_from,audio_from,audio_same_as_corpus_folder,status" > "$REP"
ok=0; bad=0; n=0
for s in $EXPECTED; do
  n=$((n+1)); printf '[%2d/31] %s ...\n' "$n" "$s"
  ft=""; fa=""
  for d in "$(home_for "$s")" "$COM" "$BNEW" "$UNSP" "$DEM" "$NBT"; do
    [ -d "$d" ] || continue
    [ -z "$ft" ] && ft=$(find "$d" -maxdepth 2 -type f -iname "$s.txt" ! -name '._*' | head -1)
    [ -z "$fa" ] && fa=$(find "$d" -maxdepth 2 -type f \( -iname "$s.wav" -o -iname "$s.mp3" \) ! -name '._*' | head -1)
  done
  status="ok"; same="NA"
  if [ -z "$ft" ] || [ -z "$fa" ]; then
    status="missing:"; [ -z "$ft" ] && status="$status transcript"; [ -z "$fa" ] && status="$status audio"
    near=$(find "$ICE" -maxdepth 4 -type f -iname "${s}*" ! -name '._*' 2>/dev/null | head -4 | tr '\n' ';')
    [ -n "$near" ] && status="$status (similar: $near)"
  else
    copy_safe "$ft" "$TXT_OUT/$s.txt" || status="copy failed (transcript)"
    ext="${fa##*.}"; ext=$(echo "$ext" | tr 'A-Z' 'a-z')
    copy_safe "$fa" "$AUD_OUT/$s.$ext" || status="copy failed (audio)"
    oldf=$(find "$OLD" -maxdepth 1 -type f -iname "$s.$ext" 2>/dev/null | head -1)
    if [ -n "$oldf" ]; then cmp -s "$oldf" "$AUD_OUT/$s.$ext" && same="yes" || same="NO"; fi
  fi
  [ "$status" = "ok" ] && ok=$((ok+1)) || { bad=$((bad+1)); echo "  $s: $status"; }
  echo "$s,\"$ft\",\"$fa\",$same,\"$status\"" >> "$REP"
done
echo; echo "Copied: $ok of 31   Problems: $bad   (details: $REP)"
echo "Audio that differs from the copy in the corpus folder: $(grep -c ',NO,' "$REP")"
echo; echo "=== Transcript audit: what MFA will see (markup and numerals need a decision before alignment)"
python3 - "$TXT_OUT" <<'EOP'
import sys, os, re, glob
print(f"{'file':10s}{'words':>7s}{'lines':>6s}{'<..>':>6s}{'[..]':>6s}{'(..)':>6s}{'digits':>7s}{'#':>5s}{'non-ASCII':>10s}  first 60 characters")
for f in sorted(glob.glob(sys.argv[1] + "/*.txt")):
    b = open(f, "rb").read()
    try: t = b.decode("utf-8-sig")
    except UnicodeDecodeError: print(f"{os.path.basename(f)[:-4]:10s} NOT UTF-8"); continue
    w = len(t.split())
    print(f"{os.path.basename(f)[:-4]:10s}{w:7d}{len(t.splitlines()):6d}{len(re.findall(r'<[^>]*>', t)):6d}{len(re.findall(r'\[[^\]]*\]', t)):6d}{len(re.findall(r'\([^)]*\)', t)):6d}{len(re.findall(r'\d+', t)):7d}{t.count('#'):5d}{sum(1 for c in t if ord(c) > 127):10d}  {' '.join(t.split())[:60]}")
EOP
