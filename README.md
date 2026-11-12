# Acoustic model choice as a source of measurement bias in Nigerian English vowel analysis

Code, settings, annotation files and derived results for the paper
*Acoustic model choice as a source of measurement bias in Nigerian English vowel analysis*

Four pronunciation dictionaries (NigE, Indian English, UK English, US English) were used with one MFA acoustic model (english_mfa, MFA 3.3.8)
to align the same Nigerian English recordings; formants were extracted with new-fave 1.2.1. A listener marked 308 vowels blind to the alignments.

## What is here

| Folder | Content |
|---|---|
| `code/R/` | `POMA_dictionary_analysis.Rmd`: every table, figure and number in the paper, with a final section that checks them against the manuscript |
| `code/shell/` | the shell scripts used to build the corpus, run MFA and new-fave |
| `code/python/` | scripts for the blind-sample draw, scoring, and the first versions of the analyses (the R document reproduces them) |
| `code/praat/` | the Praat script used for the blind annotation |
| `config/` | new-fave configuration and version, MFA version, checksums of the acoustic model and dictionaries |
| `data/annotation/` | the vowels drawn for annotation, the key, and the listener's marks |
| `data/alignment_info/` | MFA's own summary of each alignment (log-likelihood, SNR, duration deviation), the commands and logs; `round2/` holds the second batch of recordings |
| `data/dictionary/` | the custom NigE dictionary (`english_nigeria_mfa.dict`). The Indian, UK and US dictionaries and the acoustic model are the ones distributed with MFA 3.3.8 (see `config/model_and_dictionary_checksums.txt`) |
| `results/` | the tables and figures written by the R document, and the list of recordings with durations |
| `docs/` | the knitted output of the R document |

## Where each table and figure of the paper is

| Paper | File in `results/` |
|---|---|
| Table 1 | `table1_corpus_flow.csv` (the paper prints a shortened version) |
| Table 2 | `table2_alignment_output.csv` |
| Table 3 | `table3_agreement.csv` |
| Table 4 | `table4_error_types.csv` |
| Table 5 | `table5_boundaries.csv` |
| Table 6 | `table7_formant_availability.csv` |
| Table 7 | `agreement_between_dictionaries.csv` |
| Figure 1 | `figure2_category_errors_by_vowel.png` |
| Figure 2 | `figure3_confusion_matrices.png` |
| Figure 3 | `figure4_vowel_space_by_dictionary.png` |
| Supplementary Figure S1 | `figure5_labellings_of_annotated_tokens.png` |

The file names follow the numbering of the R document, which differs from the paper's numbering because one figure and one table were dropped from the paper.

## What is not here, and why

The audio recordings, their transcripts and TextGrids, and the raw formant tracks (one row every 2 ms) are not included: the recordings come from
ICE-Nigeria and other sources whose licences do not allow redistribution, and the tracks files are large. They can be regenerated from the
recordings with the scripts and settings in this repository. The data can be requested from the corresponding author.

## Reproducing the analysis

1. Install R (4.x) with `dplyr`, `tidyr`, `purrr`, `stringr`, `readr`, `tibble`, `ggplot2`, `knitr`, `rmarkdown`.
2. Edit the `config` chunk of `code/R/POMA_dictionary_analysis.Rmd` (paths to the study folder and the annotation folder).
3. Knit. The last section lists each number printed in the paper with PASS or FAIL, and compares the R scores with the Python scores.

Software: MFA 3.3.8 (conda environment `aligner`), new-fave 1.2.1 (Python virtual environment), Praat 6.4, R 4.5.0 on macOS.

## Licence and citation

Code: MIT licence (`LICENSE`). Annotation files and results: CC BY 4.0. Cite the paper; see `CITATION.cff`.
