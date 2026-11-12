#!/bin/bash
# Remove the duplicated audio from the OneDrive extension folders of Indian, UK and US (NigE keeps its copy, which the Rmd lists;
# extension_audio keeps the master). Tracks files and TextGrids are never touched.
# Usage: bash ~/free_extension_space.sh            (dry run: reports only)
#        bash ~/free_extension_space.sh delete     (deletes, only if every check passes)
OD="/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh"
B="${B:-$OD/POMA_New_20261110}"
EXT="$B/extension"
LOC="${LOC:-$HOME/mfa_work_ext}"
fsize() { stat -c%s "$1" 2>/dev/null || stat -f%z "$1"; }     # file size from metadata: reads nothing, so no OneDrive download
ok=1; total=0
for V in Indian UK US; do
  n_wav=$(ls "$EXT/$V"/*.wav 2>/dev/null | wc -l)
  n_loc=$(ls "$LOC/in/ext_$V"/*.wav 2>/dev/null | wc -l)
  n_tg=$(ls "$EXT/$V"/*.TextGrid 2>/dev/null | wc -l)
  n_tg_loc=$(ls "$LOC/out/$V"/*.TextGrid 2>/dev/null | wc -l)
  n_trk=$(ls "$EXT/fave_runs/$V"/*tracks.csv 2>/dev/null | wc -l)
  miss=0; bytes=0
  for w in "$EXT/$V"/*.wav; do
    [ -e "$w" ] || continue
    l="$LOC/in/ext_$V/$(basename "$w")"
    if [ ! -f "$l" ] || [ "$(fsize "$w")" != "$(fsize "$l")" ]; then miss=$((miss+1)); fi
    bytes=$((bytes + $(fsize "$w")))
  done
  total=$((total + bytes))
  echo "$V: $n_wav wav in OneDrive | local copies: $n_loc, without a same-size local copy: $miss | TextGrids: $n_tg (local $n_tg_loc) | tracks files: $n_trk | $((bytes/1048576)) MB"
  if [ "$n_wav" -eq 0 ]; then echo "   nothing to remove"; continue; fi
  if [ "$miss" -ne 0 ] || [ "$n_tg" -ne "$n_trk" ] || [ "$n_trk" -eq 0 ] || [ "$n_tg" -ne "$n_tg_loc" ]; then echo "   CHECK FAILED for $V: nothing will be deleted"; ok=0; fi
done
echo "Total that can be freed: $((total/1048576)) MB"
if [ "$1" = "delete" ] && [ "$ok" -eq 1 ]; then
  for V in Indian UK US; do rm -f "$EXT/$V"/*.wav; echo "$V: removed audio; left: $(ls "$EXT/$V"/*.wav 2>/dev/null | wc -l) wav, $(ls "$EXT/$V"/*.TextGrid | wc -l) TextGrids"; done
  echo "NigE keeps $(ls "$EXT/NigE"/*.wav | wc -l) wav; the master copies are in $B/extension_audio ($(ls "$B/extension_audio"/*.wav 2>/dev/null | wc -l) wav)."
else
  echo "Dry run, or a check failed: nothing was deleted."
fi
