# V6 SDPA repair: a new local engineering candidate

2026-10-16. The PI requested fixing the observed CUDA compatibility error.
This note defines prototype version 2 for local implementation and future
separately admitted hardware checks. It grants no paid launch, formal collection
or scientific numerical adoption.

The previous stage-A draft explicitly required FP32 logarithmic bias and a
recorded failure if unsupported. The first A100 test correctly recorded that
failure. That version, its FP32 requirement and its failure remain historical
facts; they are not retroactively passed or overwritten.

The new isolated `efficient_sdpa` candidate stores its additive mask in the
query dtype (BF16 or FP32), allocating padded rows before the logical-width
slice. Thus BF16 queries quantize finite log-gain values. For example, rounded
`log(0.25)` is -1.3828125 and rounded `log(0.5)` is -0.69140625; these correspond
to approximate multiplicative weights 0.250872 and 0.500871. This is an explicit
engineering precision difference, not a change to the declared gain grid.
`compiled_flex` and the packed candidate keep their FP32 score-bias arithmetic.

Both fresh operator and complete-workload packages bind `operator_bias_policy`
and this note's source hash. A missing, stale or altered policy must be refused.
Earlier packages and controllers must not be edited to accept the new sources.

The independent FP64 oracle uses the originally declared gain, including its
unrounded logarithm, and already quantized query/key/value inputs. The original
`2**-7 * value_scale` engineering ceiling stays fixed. Failure must remain
failure; no kernel fallback, widened tolerance, rounded oracle or retry is
authorized. This ceiling is not a scientific tolerance.

Retain all original 23 CUDA tests and add 24 dtype/gain/window cases. A fresh
hardware controller must bind the complete 47-case set, reject skipped or
incomplete coverage and stop on failure before model comparisons. Real-model
native checks, four-gain traces, exact unchanged Replay, full cases, backups,
actual stop and prospective scientific admission remain separate obligations.

No research sample, task, interaction, metric, selection rule, model, financial
origin or cumulative cap is changed. The closed failed trial is not reopened
by this local repair. Current hardware correctness and speed remain unmeasured.
