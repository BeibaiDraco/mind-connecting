# Provenance of the manuscript (repository file, not part of the paper)

Written 2026-09-25 when the appendix of `paper/main.tex` was made reader-facing. The appendix
no longer names run IDs, internal condition labels, files or git tags; this file keeps them so
that every number in the paper can still be traced to raw records. It is the table, cited in the
paper, that maps every figure and table to the runs it was computed from (Sections 2 and 5);
the run IDs name the directories of the trial records.

The public repository starts from a single commit made on 2026-09-25. The development history before that date, including the freeze commits and tags, is kept as a private archive (a git bundle held by the PI); commit hashes and tags mentioned in these documents refer to that archive.

## 1. Protocols and freezes

| Protocol (paper wording) | File | Git tag | Freeze manifest | Freeze commit |
|---|---|---|---|---|
| protocol of the residual-stream study | `docs/protocol/EXPERIMENT_DESIGN.md` | `protocol-v1` | `docs/protocol/FREEZE_protocol_v1.txt` | `8516829` (2026-09-24 01:26 -0500) |
| protocol of the first confirmatory sample and its companion studies | `docs/protocol/PROTOCOL_V2.md` | `protocol-v2` | `docs/protocol/FREEZE_protocol_v2.txt` | `29108fb` (2026-09-24 12:02 -0500) |
| protocol of the two-way pilot and the main sample | `docs/protocol/PROTOCOL_V3.md` | `protocol-v3` | `docs/protocol/FREEZE_protocol_v3.txt` | `5689aca` (2026-09-24 21:09 -0500) |

Each manifest records the SHA256 of every source and configuration file and the commit.
Later protocols leave earlier frozen results unchanged. Calibration, pilot and confirmatory
episodes come from disjoint splits. Result tags: `results-formal-v1`, `results-v3-confirm`.

Model: `Qwen/Qwen3-4B-Instruct-2507`, revision `cdbee75f17c01a7cc42f958dc650907174af0554`;
`transformers==4.57.1`, `tokenizers==0.22.1`.

## 2. Study map with run IDs (as in the appendix table `tab:study-map` before 2026-09-25)

| Stage (paper wording) | Internal name | New N | Run ID |
|---|---|---|---|
| Selection and signal pilots | calibration, S-*, sig-* | -- | see section 3; reports `docs/results/ALL_RESULTS.md`, `docs/results/v2/`, `docs/results/v3/` |
| Residual-stream study | v1 main | 300 | `20260924-062722_main_v1` |
| (residual-stream diagnostics, content swap) | v1 main_diag | 0 | `20260924-103817_main_diag_v1` |
| (residual-stream layer variants) | v1 ext_layers | 0 | `20260924-104223_ext_layers_v1` |
| (residual-stream support-size variants, nested masks k = 16/128/1024) | v1 ext_masks | 0 | `20260924-115148_ext_masks_v1` |
| First confirmatory sample | v2 main (D, A_K, C) | 600 | `20260924-172152_v2_main_confirm` |
| Content-swap check (60 first-confirmatory episodes, four orderings) | G2 | 0 | `20260924-192633_v2_main_diag_confirm` |
| Balanced-rehearsal sample | BAL (E) | 600 | `20260924-193405_v2_bal_confirm` |
| Dose series (300 first-confirmatory episodes, six weights) | DOSE | 0 | `20260924-210346_v2_ext_dose_confirm` |
| Two-way strength pilot | S-LIVE (S-B') | 40 | `20260924-230820_v3_s_live_strength` |
| Two-way pilot | B' | 80 | `20260925-001135_v3_sig_bprime_signal` |
| Main sample | v3 confirm (A', T3b, RF) | 600 | `20260925-021307_v3_confirm_confirm` |

Episode keys: first-confirmatory and dose-series episodes are `v2_main-0-NNNNN`; main-sample
episodes are `v3_confirm-0-NNNNN`.

## 3. Pilot and selection runs (from `docs/results/ALL_RESULTS.md`)

| Step | Run ID | What it decided |
|---|---|---|
| Baseline check (G1), first materials | `20260924-045948_g1_baseline` | behavioral endpoint (BEH) failed and was dropped (v0.5.2); capability pool changed to 18 common-knowledge questions |
| Baseline check (G1), final materials | `20260924-052150_g1_baseline` | passed; no leakage without a link |
| Calibration | `20260924-050715_calibrate_c0` | 60 calibration episodes; layers 12/18/24 |
| Pilot A | `20260924-052736_pilot_a_screen` | screening; selected raw message, layer 24, g = 0.3 (access +1.84) |
| Pilot B | `20260924-054404_pilot_b_grid` | g* = 0.2; g_s* = 0.1; N = 300 |
| Pilot C | `20260924-061858_pilot_c_recheck` | content-swap check of the residual-stream link |
| Strength pilot S-kv (round 1) | `20260924-144935_v2_s_kv_strength` | not passed: KV-ALL w = 1 gave access +8.9 but capability fell 0.19; strongest admissible point only +2.2 |
| Strength pilot S-kv2 | `20260924-151907_v2_s_kv2_strength2` | selected KV-P w = 2 |
| Steering-vector match S-static-R | `20260924-153829_v2_s_static_match-r` | STATIC 0.03 matched to the residual link |
| Steering-vector match S-static-K | `20260924-154706_v2_s_static_k_match-k` | STATIC 0.4 closest to KV-P w = 2, unmatched (+11.1 vs +18.2) |
| Balanced materials check | `20260924-154429_g1_v2-balanced` (and later balanced2) | first balanced materials failed rehearsal check; balanced2 passed |
| Signal pilot 1 | `20260924-155317_v2_sig1_signal` | B_R and A_R stopped; C went forward |
| Signal pilot 2 | `20260924-161505_v2_sig2_signal` | D, G2-KV, A_K went forward; B_K stopped |
| Signal pilot E | `20260924-164449_v2_sigE_signal` | E went forward |
| Exploratory diagnostic B | `20260924-170251_v2_diag_b_explore` | two-way fixed-memory swap; live read at w = 0.7 |
| Steering-vector match S-A' | `20260924-230325_v3_s_static_a_match` | STATIC g = 0.1 matched to KV-P w = 1 |
| Signal pilot T3 | `20260924-233653_v3_sig_t3_signal` | third-person record judged unclean (13.8% of notes used "I") |
| Signal pilot A' | `20260925-000154_v3_sig_aprime_signal` | went forward |
| Strength match S-T3b | `20260925-012116_v3_s_t3b_match` | strict third-person record at w = 0.6 matched to w = 1 |
| Signal pilot T3b | `20260925-013320_v3_sig_t3b_signal` | w = 0.6 arm judged unmatched; did not go forward |

Pilot reports: `docs/results/v2/*.md`, `docs/results/v3/*.md`.

## 4. Internal names used in run IDs, records and reports

| Internal | Paper wording |
|---|---|
| C0 | no link |
| KV-P | memory link (one-way, fixed memory) |
| KV-ALL | live loop |
| KV-PC | fixed memory plus a weak live read (w_P on prompt keys, w_C on later keys) |
| STATIC (followed by its gain) | steering vector (formerly "fixed rule vector") |
| LANG_TAG / LANG_UNTAG / LANG_SELF / LANG_STRANGER | text message tagged "B shared" / untagged / labelled "your own earlier thoughts" / labelled "a stranger" |
| FULL / RF | link kept / link cut before the question |
| ONE / TWO | one-way / two-way reading |
| 3ps / T3, T3b | third-person record / its studies |
| v1 / v2 / v3 | the three protocols; confirmatory splits = residual-stream study / first confirmatory sample / main sample |
| BAL / DOSE / G2 / B' | balanced-rehearsal sample / dose series / content-swap check / two-way pilot |
| S-LIVE | two-way strength pilot |
| START / NOW / WORD / CAP / ACC | assigned priority / current priority / code word / capability check / access questions |
| D, A_K, C, E (v2 families) | claiming vs no link / memory link vs unmatched vector / text-label contrasts / balanced rehearsal |

## 5. Figure sources (as in the appendix table `tab:figure-provenance` before 2026-09-25)

| Figure | Data | Evidence |
|---|---|---|
| 1a-c | Generated concept illustrations | Schematic |
| 1d | Dose series episode `v2_main-0-00274`; rate over the 300 coded w = 2 reports | Example; post hoc coding |
| 1e | Main-sample episode `v3_confirm-0-00068`; rate over the 165 word-matched episodes | Example; post hoc grouping |
| 1f | Two-way pilot, N = 80 | Exploratory pilot |
| 2 | Task and interface specification; generated task illustration | Schematic |
| 3a | Main and first confirmatory samples, N = 600 each | Descriptive |
| 3b-c | Dose series, N = 300; 900 blind-coded reports in three arms | Descriptive; post hoc |
| 3d | Main sample at w = 1, 1,200 answers | Post hoc |
| 4a, 4c | Generated route illustrations; card excerpts | Schematic |
| 4b | Main sample (memory link, steering vector) and first confirmatory sample (text), N = 600 each | Descriptive |
| 4d | Main sample at w = 1, self/partner pairs within ordering | Post hoc |
| 4e | First confirmatory sample, text conditions, N = 600 | Descriptive |
| 5 | Main sample, N = 600; episode `v3_confirm-0-00068` (a); groups n = 276/324 and 165/435 (c) | Example; descriptive; post hoc (c) |
| 6 | Two-way pilot, N = 80; generated illustration (a) | Schematic (a); exploratory pilot (b, c) |

Run IDs for each sample are in section 2. Plotted choice rates weight episodes equally after
averaging the two orderings; intervals for prespecified logit and excess contrasts are copied
from the frozen analysis outputs.

## 6. Records and analysis files

- Each raw run directory keeps `identity.json`, `manifest.json`, a copy of its configuration
  (`config.yaml`), append-only `records/attempt-*.jsonl`, and tick logs (`ticks.jsonl`, `ticks/*.npz`).
- Derived files include `contrasts.json`, `signal.json`, `pair_signal.json`, and completeness
  reports (`completeness.json`, `run_status.json`).
- Study reports: `docs/results/` (residual-stream study: `docs/results/formal_report.md`, which
  also holds the layer comparison, the support-size extension and the control arms).
- Post hoc analyses: `docs/results/story_checks.md`, generated by `scripts/explore_story_checks.py`.
- Figure code: `scripts/make_story_figures.py`; plotted values with their run IDs:
  `paper/figures/story_numbers.json`.
- Reference checks: `paper/refs_verification.md`.
- The manuscript builds with `make -C paper`.
