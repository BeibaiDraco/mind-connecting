# Summary of results from the formal experiment (protocol-v1)

Date: 2026-09-24. Data: `20260924-062722_main_v1` (300 episodes × 20 conditions, 223,500 trials, all complete),
`20260924-103817_main_diag_v1`, `20260924-104223_ext_layers_v1`, `20260924-115148_ext_masks_v1`, none with missing data.
Full numbers are in [formal_report.md](formal_report.md) (preregistered part first) and [formal_exploratory.md](formal_exploratory.md) (post hoc exploration).

## 1. The three preregistered comparisons (receiver A, primary metric M, N = 300)

| Comparison | Difference (nat) | 95% CI | Holm p | Conclusion |
|---|---|---|---|---|
| TWO(g\*) − ONE(g\*) | −0.07 | [−0.21, +0.07] | 0.31 | No difference; the interval rules out effects > 0.21 nat |
| ONE(g\*) − STATIC(g_s\*) | +0.18 | [−0.02, +0.40] | 0.19 | Not significant; the trimmed mean has the opposite sign, and the two are not matched in strength |
| ONE(g\*) − LANG-tag | +0.85 | [+0.54, +1.20] | < 0.001 | Significant; mainly driven by LANG-tag lowering M (−1.0), i.e. language with a source tag makes the boundary clearer |

Secondary metric family (M_NOW, M_WORD): ONE − STATIC is significant on M_NOW (STATIC lowers M_NOW); TWO − ONE is positive in direction on M_NOW (+0.19, Holm p = 0.17) and M_WORD (+0.14, Holm p = 0.11), but not significant after correction.

## 2. Main findings (descriptive and exploratory, not confirmatory conclusions)

1. **The hidden-state bridge carries real content, and more of it as gain rises.** ONE's ACC increment is +0.16 → +0.83 nat (g = 0.05 → 0.3). Content counterfactual in the diagnostic subset of the formal sample: rule +0.70 (lower bound +0.24), secret word +0.41 (lower bound +0.09); both pass. After a random-rotation encoding (SCRAM) the transfer weakens sharply, which shows it relies on the shared coordinate encoding.
2. **The content carries no source, and it is not claimed as one's own either.** At baseline, the model's grip on its own rule is 33.5 nat higher than on the partner's rule. The bridge only raises the partner's rule by about 2–4 nat on both questions at once, "what was I assigned" and "what was Robin assigned"; it is not self-specific, and the self-judgment is never flipped (START 100% correct). M instead falls slightly with gain (−0.05 → −0.29).
   - Caveat: the model's own rule was rehearsed in the note and the reflection, while Robin's was not; this asymmetry may make it easier for a generic perturbation to move the Robin question.
3. **Untagged language is taken as "mine".** For the same passage of B's reflection, when no source is given (LANG-untag): M +9.8 nat, M_NOW +27 nat; 46% of the time A takes the partner's priority as "the one I am using now", and 15% of the time it says it was assigned the partner's rule. When the text says "from a certain code name" (LANG-tag), A knows the partner's rule (ACC +29 nat) yet separates them more clearly (M −1.0).
4. **Early signs from the two-way link.** TWO makes A's and B's internal states converge (cosine +0.08 to +0.13, versus +0.04 to +0.05 for one-way). On "which priority am I using now", TWO shows a self-specific shift (M_NOW: +0.23 [0.03, 0.44] at g = 0.2, +0.39 [0.10, 0.68] at g = 0.3), while ONE does not. This is secondary or exploratory evidence.
5. **The influence exists only while the link is on.** Cutting the link while reading the question (RF) makes the M and ACC effects disappear; linking only while reading the question (RO) gives effects comparable to linking throughout. The self-report is the exception: under RF, the share choosing "two or partly shared" is still about 4% higher.
6. **Self-report.** One-way, static and language links all raise the share of "two subjects or partly shared" by 2–9 percentage points; the two-way link does not.
7. **Where to link and how much.** For one-way, layer 24 transfers best. The injection dimension has to be ≥ 1024 (out of 2560) for content to get through; at ≤ 128, even with the energy topped up, it is almost zero. No condition impaired capability (CAP ≥ 0.97) or answer format.

## 3. In one sentence

Within the strength the model can tolerate, the hidden-state bridge carries a little real content across, but it only "gets mixed in" and does not become "mine". What really makes the model take someone else's intent as its own is language without a source tag. The "merging into one" of the original idea did not appear, mainly because the bridge is too weak: at safe gains the perturbation is only about one tenth of the self-judgment margin.

## 4. Feasible follow-up directions (each must be written up as a new protocol version and approved by the PI)

| Direction | What to do | What it answers | GPU time |
|---|---|---|---|
| A. Strength-matched STATIC | Set the STATIC gain to 0.01–0.05, align it with ONE's ACC, and redo "live state vs static direction" | Makes the second confirmatory comparison fair | About 1 hour |
| B. Two-way "current intent" recheck | Preregister TWO vs ONE with M_NOW as the primary metric (g = 0.3, N ≈ 600) | Tests whether the early sign in point 4 is real | About 2 hours |
| C. Source-tag gradient (language) | Several ways of stating the source: no tag, a code name, "your own earlier thought", "a stranger", etc. | Characterizes "what makes content become mine" | About 1 hour |
| D. A stronger bridge (v2 interface) | KV sharing (A's attention reads B's cache directly) or interpolated writing | Whether the boundary still holds when content flows in massively | About 1 day to implement plus review, half a day to run |
| E. Rehearsal-balanced materials | Have Robin's rule rehearsed to the same degree | Removes the risk of asymmetry in M | About 2 hours |

Recommendation: do A + B + C first (about 4 GPU hours in total, and each directly strengthens the paper), then decide whether to invest in D. Along the main line "the bridge transmits content but not ownership", the existing results are already enough for a solid arXiv paper; D is the direction that further answers "would a truly strong link produce merging into one".
