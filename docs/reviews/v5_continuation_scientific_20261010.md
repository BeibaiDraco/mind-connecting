# V5 continuation scientific review — 2026-10-10

## Scope and current conclusion

This is a review of local preparation for
[the separate continuation protocol](../protocol/PROTOCOL_V5_CONTINUATION.md),
not an authorization to restart a GPU. It preserves the original v5 failed
prerequisites and proposes two fixed Llama formal comparisons, each N600, for
final package ratification. No formal Qwen attribution outcome or significance
was read to choose the continuation.

The protocol received an independent read-only review by the agent responsible
for the CF validator repair. No scientific or authorization conflict was found;
the exception table was clarified to say that its named exceptions await final
package ratification. The protocol author independently reviewed the CF repair,
continuation module and preparation/freeze scripts, including actual historical
audits and both emitted configuration roundtrips. **No remaining scientific
blocker was found in this local preparation.** This is not a paid-launch pass.

## Scientific boundaries checked

- The exceptions name the observed ordinary-KV provenance CAP loss of 5.625
  points and the STATIC-study ordinary-KV/CF losses of 6.25/5.9375 points. They
  do not define a new general cutoff or retrospectively pass original v5.
- Provenance comes first, followed by the previously selected layer16/raw/g0.5
  STATIC comparison. No new selection, pilot sample, prompt, model or mechanism
  study is introduced. Both formal samples remain fixed at 600 episodes.
- Original baseline, access, content, matching, format and record-integrity
  requirements remain. Existing N80 samples are development evidence for this
  amendment, not independent validation of a subsequently accepted tolerance.
- Original v5 Qwen results retain the original Holm2/Holm6 families with the
  failed Llama slots unavailable. Amended Llama uses separate reports with the
  same conservative family sizes and non-estimated p=1 slots. No old missing
  effect is filled in, no episodes are pooled, and no report is selected by
  significance. STATIC retains one primary M test and a separate Holm2 family
  for M_NOW/M_WORD.
- Fresh formal CAP and matching drift affect interpretation rather than sample
  inclusion, reselection or effect-based stopping. Neither capability
  preservation, formal equivalence, a special self mechanism nor a positional
  mechanism is established by these comparisons.
- Local preparation and budget flexibility do not authorize paid launch. The
  final package needs a numerical spending/deadline contract retaining prior
  expenditure, explicit PI launch instruction and verified backup/stop controls.

## Material independence and unused splits

The preparation check regenerated the intended seed-0 splits using the frozen
task generator and the original preflight physical-material hash. This hash
removes episode ID, split name, index, answer rotations and the unused second
scenario before comparing materials; renamed samples cannot pass as fresh ones.

Both sets contain 600 distinct episodes, are mutually disjoint, and have no
overlap with materials from 41 historical configurations or the other ten v5
splits. The frozen split-manifest content hashes reproduce exactly:

| Split | Content hash | Episode-ID hash |
|---|---|---|
| `v5_llama31_provenance_confirm` | `6778957754fb0a3a` | `d529d93458fe219f` |
| `v5_llama_static_confirm` | `1ecf0b1bc68620fb` | `f8c3929ab61d7c27` |

Only `identity.json` metadata were inspected in 56 mirrored SD runs; neither
target split had a run identity. This check did not read formal outcomes.
The execution preflight must still check the authoritative remote inventory
before first launch and refuse any ambiguous prior run.

## CF checker repair review

The narrow change to `v5_static._checked_records` derives expected CF question
metadata from `tasks.make_donor_variant(ep, "CF").donor_episode`, matching the
unchanged producer. Expected fixed physical r0/r1 candidates still come from
the original episode. The statistical function, thresholds, donor generation,
rendered model inputs and runtime remain unchanged.

The new test fixture uses the actual Runner donor, pending-question and base-
record builders, with token serialization stubbed because this is a metadata
test. It checks unchanged physical questions, correct CF partner/spare labels,
and rejection of exchanged original/CF meanings, corrupted options, text hashes
and physical candidates. Existing synthetic CF fixtures were corrected to match
those same producer semantics without changing their physical logit examples.
Independent focused run: **34 tests passed**.

This repair does not change the recovered original verdict. The independent
producer-aware audit and the unchanged gate computation remain documented in
[the original terminal audit](v5_static_terminal_audit_20261010.md). Old source
identities must be verified at their own frozen source version; a repaired
checkout must not masquerade as the original algorithm.

## Continuation implementation review

Read-only review covered `src/mb/v5_continuation.py`,
`scripts/prepare_v5_continuation.py` and `scripts/freeze_v5_continuation.py`.
The historical adapter verifies the original Git tree and freeze, reconstructs
native identity, audits raw questions/physical candidates and complete ledgers,
and reruns the original numerical gates. It admits exactly the named observed
capability failures while retaining all other requirements. It does not trust
an edited saved pass flag. The recorded STATIC checker failure remains separate.

Independent calls against the real SD copies passed for the provenance chain
(290 inventoried files) and STATIC chain (984 files). Both emitted YAML files
also passed `verify_config_contract` against those raw prerequisites. They have
the fixed 600/3/12 and 600/3/10 episode/arm/readout contracts, new continuation
tags and no legacy automatic postprocessing. The new launcher dispatches their
separate continuation validator and analyzer explicitly. Formal completion is
determined by usable complete data, not an effect, capability drift or matching
success in the new observations.

The separate analyzer retains the original formulas and invokes the provenance
combiner with Qwen unavailable in the amended report. It does not consume Qwen
formal outcomes or replace its historical inference. The STATIC primary and
secondary families are unchanged. The preparation script checks all materials
before writing new artifacts and refuses replacements; the freezer requires
committed inputs and separately records historical prerequisite pins.

The implementation author reports 42 passing targeted checks at this review
checkpoint, including wrong exceptions, additional failed gates, identity and
raw-record corruption, configuration roundtrips, dependency changes, preexisting
formal splits and write-once behavior. Its real native-tokenizer material
preflight covers 1,200 episodes and 26,400 question/ordering checks against 46
distinct prior material splits. The completed shared offline suite passed
**426 tests, with five skipped**. The reviewed continuation module SHA256 is
`98599ecac364b11616c6a27978ea0375d50ce57b148c6dfa45227a4ac83470fb`.
Additional deployment checks are recorded by the integration review.

## Operational boundary

An additional independent review of the private continuation guard checked inert
proposals, exact approval scope/cap, preserved prior spending anchors and
reserves, local and remote deadlines, bounded commissioning handoff and stop
behavior after evidence-write failure. Its 26 offline mocked checks passed.
Reviewed helper SHA256:
`e1014c1b5f74ef44d1bf4f74e93064c0b755617649e44887bd88ac3bae01dcfe`.
No real provider, process-launch, network or model operation was performed in
that review; mocks do not certify future host availability.

Actual GPU acceptance on the new source freeze, deployment, budget activation
and collection have not occurred for this continuation. Final ratification,
numerical spending approval and an explicit launch instruction remain necessary.
