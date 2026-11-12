# annotate_blind_sample.praat
# Steps through one batch of the blind vowel sample. For each row it opens the recording
# in the Sound editor, zoomed to the time window. You drag over the vowel, pick the label,
# and the script saves onset, offset and label. It reads only the .wav files, never a TextGrid.
form Blind vowel annotation
    sentence Audio_folder /Users/oamoniyan/annotation_audio
    sentence Batch_file /Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh/POMA_New_20261110/blind_sample_v2/batch_1.csv
    sentence Output_file /Users/oamoniyan/Library/CloudStorage/OneDrive-UniversityofPittsburgh/POMA_New_20261110/blind_sample_v2/batch_1_annotated.tsv
    natural Start_at_row 1
endform

Text writing preferences: "UTF-8"
if fileReadable(output_file$)
    table = Read Table from tab-separated file: output_file$
    appendInfoLine: "Resuming from ", output_file$
else
    table = Read Table from comma-separated file: batch_file$
endif
n = Get number of rows
stopNow = 0
done = 0

for i from start_at_row to n
    if stopNow = 0
        selectObject: table
        onset$ = Get value: i, "onset_s"
        status$ = Get value: i, "label"
        todo = 1
        if onset$ <> "" and onset$ <> "--undefined--"
            todo = 0
        endif
        if status$ <> ""
            todo = 0
        endif
        if todo = 1
            file$ = Get value: i, "file"
            word$ = Get value: i, "word"
            k$ = Get value: i, "vowel_in_word"
            ws$ = Get value: i, "window_start"
            we$ = Get value: i, "window_end"
            ws = number(ws$)
            we = number(we$)
            audio$ = audio_folder$ + "/" + file$ + ".wav"
            if fileReadable(audio$)
                sound = Read from file: audio$
                totalDur = Get total duration
                if we > totalDur
                    we = totalDur
                endif
                View & Edit
                editor: sound
                    Zoom: ws, we
                endeditor
                valid = 0
                repeat
                    beginPause: "Token " + string$(i) + " of " + string$(n)
                        comment: "Recording: " + file$
                        comment: "Word: " + word$ + "      vowel number " + k$ + " in the word"
                        comment: "1. In the editor, drag across the vowel on the waveform to select it."
                        comment: "2. Choose the vowel you hear, then click Save and next."
                        choice: "Vowel", 1
                            option: "a"
                            option: "aː"
                            option: "e"
                            option: "i"
                            option: "iː"
                            option: "o"
                            option: "u"
                            option: "uː"
                            option: "ɔ"
                            option: "ɛ"
                            option: "ɛː"
                            option: "ʊ"
                            option: "ɜ"
                            option: "ə"
                            option: "other (type below)"
                            option: "cannot judge"
                        sentence: "Type if other", ""
                        sentence: "Notes", ""
                    clicked = endPause: "Stop", "Save and next", 2, 1
                    if clicked = 1
                        stopNow = 1
                        valid = 1
                    elsif vowel$ = "cannot judge"
                        selectObject: table
                        Set string value: i, "label", "UNSURE"
                        Set string value: i, "notes", notes$
                        Save as tab-separated file: output_file$
                        done = done + 1
                        valid = 1
                    else
                        editor: sound
                            selStart = Get start of selection
                            selEnd = Get end of selection
                        endeditor
                        if selEnd - selStart < 0.02 or selEnd - selStart > 0.6
                            beginPause: "No vowel selected"
                                comment: "Drag across the vowel (20 to 600 ms) on the waveform, then continue."
                            endPause: "OK", 1
                        else
                            final$ = vowel$
                            if vowel$ = "other (type below)"
                                final$ = type_if_other$
                            endif
                            selectObject: table
                            Set numeric value: i, "onset_s", selStart
                            Set numeric value: i, "offset_s", selEnd
                            Set string value: i, "label", final$
                            Set string value: i, "notes", notes$
                            Save as tab-separated file: output_file$
                            done = done + 1
                            valid = 1
                        endif
                    endif
                until valid
                removeObject: sound
            else
                appendInfoLine: "Audio not found: ", audio$
            endif
        endif
    endif
endfor

selectObject: table
Save as tab-separated file: output_file$
appendInfoLine: "Saved ", done, " tokens in this session. Output: ", output_file$
