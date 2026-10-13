# V6 local implementation review

Date: 2026-10-12 (Chicago). Scope: the unfrozen continuous-interaction draft's
local implementation. No model inference, GPU, paid resource, new automation,
paper edit or scientific freeze occurred.

## Verdict

The first local implementation milestone passes its offline checks and
independent module reviews. It is not ready for unattended scientific execution:
neutral admission collection and exact candidate rules are unresolved; native
hardware and durable end-to-end resume acceptance have not been run. See
`docs/protocol/V6_IMPLEMENTATION_NOTES.md` for those explicit boundaries and
`docs/runbooks/V6_LOCAL_HANDOFF.md` for the remaining sequence.

## Independent review and fixes

Four agents worked on disjoint files, with the coordinating agent integrating
and committing. Authors did not solely review their own core components:

| Area | Independent review | Findings and disposition |
|---|---|---|
| Task materials, visibility and transitions | Native author reviewed task author's module | No blocking issue found; full joint balancing limits remain explicit |
| Native generation, exact attention, sealed probes and continuation | Task author reviewed native author's module | No blocking issue found in inspected code and offline contracts; CUDA correctness unverified |
| Scoring and multiplicity | Task author reviewed analysis author's module | Verified late goal-score scaling and exact all-correct trajectory equality |
| Scheduler and ledger | Task and analysis authors reviewed coordinator's modules | Added partial-ledger validation before any resumed write and a q1 LIVE/natural continuation equivalence regression |
| Native state/export serialization | Task author reviewed native author at source SHA `639cad46d30824ecdb6f108ff2e57f33b796d7a2299a78910e34bbe754658b3f` | CPU schema, inner checksums, model parameter identity, seals and owner rebinding inspected; 34 offline native tests independently passed |
| Pair/tape archive sink and final hardening | Analysis author reviewed coordinator's modules | All 16 artifact sites accounted for; verified inventory-wide hash/size admission before append; corruption leaves retained files byte-identical |

Other resolved issues during implementation include preserving the actual
native-precision action separately from FP32 diagnostics, rejecting native
control spellings in text content, distinguishing fixed pulse candidates from
actual-world correctness, and never treating missing technical observations as
incorrect model answers.

## Executed checks

- Full offline suite: **543 passed, six skipped**. This adds 115 passing V6 tests
  to the previous 428. CUDA test modules remain unexecuted.
- Complete 64-work / 16-preparation / 16-window synthetic integration: two base
  episodes and one text episode under each model schema; **680/680 rows per
  schema**, 1,360 total. Both complete resumes preserve every file byte. The
  exact analysis accepts the ledger structure but marks its result synthetic,
  source-unverified and not scientifically consumable.
- Material generation: each model has 60 baseline, three sets of 40 calibration,
  80 validation and 240 formal draft episodes, with 60 text episodes selected
  from its formal set. All substantive base materials are distinct across
  stages and model profiles. Nonformal sets are main-task skeletons, not usable
  neutral-admission data.
- Real local tokenizer audits: Qwen **15,360** native answer prefixes / **61,440**
  label append checks; Llama **15,357** / **61,428**, each on its complete N240
  draft materials. No reported errors. Private update envelopes are 38 tokens;
  question suffix lengths are 43, 50, 58, 60 or 97 for both tokenizers. This
  verifies rendered prefixes, not generated-cache continuation or task ability.
- The primitive archive integration fixture writes and reloads all 16 pair/tape
  artifacts, verifies exact no-op reuse, and rejects tampering. This fixture
  does not serialize real torch tensors. Native CUDA tensor roundtrip, control
  recovery, cross-weight rejection and replay regressions are written but unrun.

## Exact-analysis simulation

The simulation exercises the complete synthetic-ledger validator, episode
scores, bootstrap and Holm families, with N240 per schema, 50 null repetitions,
data seed 0 and 200 bootstrap draws. The joint response-quality null couples the
endpoint choices to give zero expectation; independent random endpoints would
instead give a negative conservative minimum score.

The primary family falsely rejects in 1/50 repetitions (2%; exact binomial 95%
interval **0.051%–10.647%**). The secondary family rejects in 2/50, and the
sustained-response conjunction in 0/50. The strong designed alternative meets
the sustained-response criterion for both schemas. The nonspecific-switch
rival does not: its chain-quality means are zero even though several raw
change/path contrasts are positive. These are useful regression checks, not a
proof of finite-sample size or empirical power. No simulation was used to select
model parameters, increase N or authorize spending.

## Artifact provenance

These are temporary, reproducible engineering artifacts, not scientific runs:

| Artifact | Location / SHA256 |
|---|---|
| Final materials and native tokenizer audit | `/private/tmp/mb-v6-local-final-20261012-materials/` |
| Printed final preflight | `/private/tmp/mb-v6-local-final-20261012-preflight.json`; `8ef478182352d2e7168b0ee2b0094dcea4f9dd007683a9280c401bcc899b5a65` |
| Full-clock fixture and no-op resume | `/private/tmp/mb-v6-local-final-20261012-dryrun/` |
| Exact-analysis simulation | `/private/tmp/mb-v6-local-20261012-analysis-simulation.json`; `d88ea2e95db320421bedcd338f9ef44039d2123ff1878437d69a2eb42f6a5159` |
| Qwen draft N240 materials | `e184b4bd1076fe62c2bd17740f4a541d2d98668833a57e2fea840b0e9b929134` |
| Llama draft N240 materials | `2cfaeee3142563f0ea284cdb51b3e731c6a4405bfe22385b7c9bf9cbe21acc67` |

The preflight includes hashes of 14 execution/design inputs. These identities
serve local reproducibility, not an approved formal freeze. The checked draft
config keeps the selected gain, neutral contract and financial authorization
unset. No old CAP exception, budget or outcome is inherited by V6.
