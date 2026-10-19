# Local review: isolated V6 task-clarity preparation

Date: 2026-10-19. Scope: author code/data review and offline checks; no independent
agent review or hardware/model validation is claimed.

## Changes

Added an isolated torch-free module for P0/P1/P2 prompts, balanced short/history
materials, backend-injected OFF-only diagnostic collectors and raw record
validators. Added a local-only bundle writer, targeted tests and the runbook
`docs/runbooks/V6_TASK_CLARITY_LOCAL_20261019.md`. No existing frozen scientific
file, model implementation, selector, control process, automation, budget or
provider state was changed.

P0 reproduces old prompts. P1 clarifies that goal labels select rules, that the
partner beacon is the relevant input, and that the consequence table is applied
after the button choice. P2 also renders the same table as explicit conditionals.
No note-format/generation-length change was bundled in. Neither candidate has
been tested on a real model yet.

## Checked properties

- Exact original P0 system/private/action strings on all 64 short cases; unchanged
  private messages and correct candidate/answer mappings for all variants.
- Explicit P2 rules agree with independently parsed P0 tables for every action
  and goal-name permutation (576 codebook combinations). The consequence table
  remains byte-identical.
- Short allocation: eight codebooks and all goal/partner-beacon cells per book;
  every literal target cell has balanced roles and own/partner agreement. Native
  correct choice IDs are 16/16/16/16. History allocation: eight separate episodes,
  each early focal side has all four initial beacon pairs, and literal initial
  goals occur twice per physical side. This explicitly avoids the old generator's
  first-small-block early-side imbalance.
- Ordinary private/action prompts do not leak partner beacon. Only discarded
  full-information diagnostics add true partner state and/or the public table.
- Short collection generates no work/preparation token and commits no answer.
  Its explicit empty assistant turn plus question matches official local Qwen
  native serialization for all 192 variant/case prefixes; each of four numeric
  answers appends as its intended single ordinary token.
- History collection retains 16 preparation and 64 work tokens, uses no incoming
  state, and commits only the ordinary action after both answers are sealed.
  Native invalid answers remain invalid; worlds are rebuilt from real answers.
  A deliberate parent-mutation test is rejected before publishing a result.
- Real collection requires explicit actual backend/model binding and persistent
  sinks, including a token-history sink for the history diagnostic. There is no
  model factory, rental, GPU executable, scientific-stage dispatcher, retry loop,
  prompt selector or automatic continuation in the new code.
- Raw result validation rejects incomplete/duplicate or wrong-world/question/
  native-choice records. This establishes data consistency, not model ability.
- The existing closed timing package's **75 scientific source pins remain exact**.

## Verification and artifacts

Targeted checks: **12 passed**. Entire offline suite: **1,246 passed, 10 skipped,
one GPU test deselected**, 45.26 seconds.

Separate software-only collection covered all three variants: 384 short synthetic
records across two backend labels and 1,152 history synthetic records. JSON-round-
tripped records passed complete question/world/actual-action validation. These are
software fixtures, not measurements of Qwen, backend equivalence or accuracy.
No torch was imported and no model was run.

Prepared private bundle:
`/private/tmp/mb-v6-task-clarity-20261019/prepared-01/`.
Manifest SHA256:
`7d3d5390bc43818bb688e28ac255f9faf3b99b2e5341f12ab356785c76e4579c`.
The bundle contains 192 complete short inputs, matching materials, eight history
materials and source/file checksums. `verify_local.py` and
`offline_validation.json` in its parent directory reproduce local checks.
A separate SD copy is hash-verified; no old evidence is replaced.

## Boundary and next step

The PI's agreement to improve the task is implemented as local candidate
preparation. The suggested 58/64 and 87/96 development screens, backend numerical
contract and a fresh finite paid trial still need prospective binding. The
manifest marks thresholds unratified, history variant unselected, launch false,
and automatic continuation false. The old frozen scientific gates remain intact.

The small short-question comparison is the immediate next proposed hardware
scope, not another complete timing campaign. Only after interpretable task
performance should the held-out history and then core interaction checks be
considered. There is no measured runtime, accuracy improvement, bridge finding or
scientific-adoption claim from this offline preparation.
