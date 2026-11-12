#!/bin/bash
OD="${OD:-/Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh}"
D="$OD/POMA_New_20261110/blind_sample_v2"
AUD="${AUD:-$HOME/annotation_audio}"
PK="$HOME/second_annotator_package"
rm -rf "$PK"; mkdir -p "$PK/audio"
cp "$D/reliability_second_annotator.csv" "$PK/" || { echo "reliability_second_annotator.csv not found"; exit 1; }
cp "$HOME/annotate_blind_sample.praat" "$PK/" 2>/dev/null
tail -n +2 "$PK/reliability_second_annotator.csv" | cut -d, -f2 | sort -u | while read -r s; do
  cp "$AUD/$s.wav" "$PK/audio/" 2>/dev/null || echo "audio missing: $s"
done
cat > "$PK/INSTRUCTIONS.txt" <<'EOT'
Vowel annotation: instructions

What to do
For each row of reliability_second_annotator.csv you mark ONE vowel in ONE word and say which vowel it is.
Please do not look at any forced-alignment output or TextGrid, and do not discuss individual tokens with the first annotator until you finish.

Setup (Praat 6.0 or later)
1. Open Praat. Choose Praat > Open Praat script... and open annotate_blind_sample.praat (or paste its text into Praat > New Praat script).
2. Press Cmd+R (Ctrl+R on Windows). In the form set:
   Audio folder: the full path of the "audio" folder in this package
   Batch file:   the full path of reliability_second_annotator.csv
   Output file:  a new path ending in _annotated.tsv, for example reliability_second_annotator_annotated.tsv
3. For each token a Sound editor opens zoomed to a time window and a small window asks for the label.

For each token
- Find the word named in the row inside the window (the window is padded at random, so the word is not at its centre).
- Count the vowels of the word BY EAR, from left to right. A diphthong counts as ONE vowel. The row tells you which one: vowel_in_word.
- Drag across that vowel in the waveform: from the first clear period of vowel voicing to the last period before the next sound. Keep your criteria the same for every token.
- Choose the vowel you hear in the list and click "Save and next". Use "other" and type a symbol if none fits.
- If you hear no vowel in that position (for example a syllabic l), or the word does not match what you hear, choose "cannot judge" and write a short note.
The output is saved after every token. To continue after a break, run the script again with the same three paths.

Time: about 1 to 1.5 minutes per token, about 2 hours in total. Please work in sessions of 25 to 30 tokens.

When you finish, send back the _annotated.tsv file only.
EOT
(cd "$HOME" && rm -f second_annotator_package.zip && zip -qr second_annotator_package.zip second_annotator_package)
echo "Package: $PK ($(ls "$PK/audio" | wc -l) recordings, $(du -sh "$PK" | cut -f1))"
echo "Zip: $HOME/second_annotator_package.zip"
