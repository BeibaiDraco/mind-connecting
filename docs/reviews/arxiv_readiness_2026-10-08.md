# arXiv submission readiness audit - 2026-10-08

Reviewer: Codex, with independent manuscript, PDF, and official-requirements checks.
Manuscript baseline: public commit `264222f`; manuscript and figure contents were not changed in this audit.

## Conclusion

The source package is technically ready for an arXiv upload trial. Final submission is still pending: clarify one repeated methodological description, repair a minor figure-label overflow, complete the PI's final read-through, and confirm the account eligibility, category, and license. Local compilation does not establish acceptance or successful processing by arXiv. No submission or publication was performed.

The audit does not identify a need for another experiment or a second model before the planned first version. This is a submission-readiness review, not a fresh validation of every result against raw records.

## Verified materials

| Item | Result and scope |
|---|---|
| Manuscript | `paper/main.pdf`: 35 pages, six main figures, 14 tables; source and appendices present |
| Source archive | `paper/arxiv.tar.gz`: 22 regular files, 3,636,189 bytes compressed, 3,767,556 bytes uncompressed; `main.tex`, `main.bbl`, 14 section files, six PDF figures |
| Independent build | Extracted to an empty temporary directory; three successful pdfLaTeX passes with shell escape disabled and no project input paths; extracted text exactly matches the existing manuscript PDF |
| Final build diagnostics | No missing references/citations, overfull/underfull boxes, or TeX errors; only the expected epstopdf shell-escape-disabled warning, with no EPS figures requiring conversion |
| Archive/source agreement | Every packaged file matches its repository-working-tree counterpart byte for byte |
| Abstract metadata | Converted from source: 222 whitespace-delimited words, 1,302 ASCII characters, below the official 1,920-character limit |
| Author metadata | Yunlong Xu; University of Chicago; dracoxu@uchicago.edu; present in the manuscript, subject to PI confirmation of current accuracy |
| References | All 48 citation keys are in `refs.bib` and have entries in `refs_verification.md`; this audit checked coverage, not every original publication again |
| AI statement | Text, code, analyses, report coding, and GPT-generated schematic illustrations disclosed; human responsibility and no AI authorship stated |
| Reproducibility | Code repository publicly accessible; manuscript accurately describes trial records, coding materials, and original development archive as available on request |
| Offline suite | `.venv/bin/pytest -m 'not gpu'`: 151 passed, 3 skipped |

The abstract limit and metadata rules are from [arXiv's metadata guidance](https://info.arxiv.org/help/prep.html). Public accessibility of the [code repository](https://github.com/BeibaiDraco/mind-connecting) was checked during this audit.

PDF review covered contact sheets of all 35 pages and enlarged inspection of the title page, references, all six figures, and all 14 tables. All 28 fonts are embedded with Unicode mappings; none are Type 3. The PDF is unencrypted, with no JavaScript or forms. All 393 internal link targets exist; 43 external links contain no local file paths, but were not individually visited. Apart from the Figure 1e issue below, no obvious clipping, overlap, or unreadable table was found.

## Corrections recommended before final submission

### 1. State the actual matching measure consistently

`paper/sections/setup.tex:98-102` describes the matched quantity as how often A names B's rule. `paper/sections/results.tex:104-109` similarly describes choosing the gain to match answer frequency. `paper/sections/introduction.tex:157-160` associates matching with the 15%/20% answer rates. In `paper/main.tex:79`, "that measure" is also ambiguous and can refer back to claiming.

The implemented and prespecified quantity is **mean access gain relative to C0**, based on the logit difference between B's answer and an unused distractor, not the proportion of argmax answers naming B. The confirmatory gains are 4.081 and 4.179 nats; the answer rates are 19.8% and 15.3%, respectively. The rates are descriptive outcomes, not the selection criterion.

Evidence: `paper/sections/appendix.tex:193-197`, `paper/sections/appendix_evidence.tex:150-151`, `docs/protocol/PROTOCOL_V3.md:92-97`, `src/mb/readouts.py:29-35`, `src/mb/run.py:1216`, and `src/mb/run.py:1265-1302`.

Suggested wording, for PI review; not applied:

- Abstract: replace "a steering vector matched to it on that measure in none" with "a steering vector matched on an access score in none".
- Setup: "We set its gain to match the memory link at $w=1$ in mean access gain, computed from answer logits (Appendix~\ref{app:stats}), because no gain in our grid matched the stronger link at $w=2$. Matching access gain holds one measure of arrival fixed while the route changes."
- Results opening: describe the routes as "matched in access gain" and say "We set the steering vector's gain to match the mean increase in the access score under the memory link at $w=1$."
- Introduction: "A steering vector matched the link on an access score when B's memory had no extra weight (the shares of answers naming B's rule were 15\% and 20\%), yet the link made A claim that rule in about half of its answers and the vector never."
- Figure 4 caption: specify "matched in mean access gain"; introduce the subsequent answer rates with "With the access gains matched".

These corrections preserve all numbers, analyses, and conclusions. They address a scientific-description issue, not a TeX processing failure.

### 2. Shorten or wrap the Figure 1e label

On PDF page 2, Figure 1e's line ending in "code word: dragon" extends beyond its panel's right border toward panel f. The source is `scripts/make_story_figures.py:447-448`. Shorten the prefix or split the annotation over two lines while preserving its meaning. This is a minor visual defect. It was not edited during this audit; regenerate the figure and PDF after the change, then rebuild the submission archive.

## Packaging fix completed

The original macOS-created archive contained 22 AppleDouble `._*` metadata files in addition to its 22 intended inputs. macOS `tar -tzf` did not display those metadata entries, but Python's `tarfile` inventory exposed them.

`paper/Makefile` now sets `COPYFILE_DISABLE=1` for packaging. The rebuilt archive contains exactly the 22 intended regular files and no hidden metadata files. The outdated comment claiming that arXiv never runs BibTeX was corrected: the local `.bbl` is bundled to preserve the reviewed bibliography. Current arXiv supports `.bib` processing and prefers a supplied, correctly named `.bbl`; see [TeX submission guidance](https://info.arxiv.org/help/submit_tex.html).

Rebuilt archive SHA256:

```text
c91bd8d9c3f4633d9e6f47058d09c08a38c37be06284e4d78a564fe883835b21
```

Unchanged manuscript PDF SHA256:

```text
ee1b5c4397cacffe7b4ee5525b5cfddf553a9b1e51c2584b37756179b666ea87
```

These identify the audited artifacts; a later rebuild after manuscript changes will need new verification.

## Account and submission decisions still unverified

1. **Account and endorsement.** No authenticated arXiv account was inspected. Since January 21, 2026, an institutional email alone does not qualify a new submitter for automatic endorsement; the automatic path also requires previous authorship in the relevant endorsement domain. Otherwise, an eligible established author must personally endorse the submitter. Existing endorsements remain valid. See the [official update](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/) and [endorsement instructions](https://info.arxiv.org/help/endorsement.html). The PI was asked about existing eligibility; it remains unconfirmed in this audit.

2. **Submission quota.** Current policy permits two new submissions per calendar month and at most three active submissions. Account usage was not checked. See [submission-rate policy](https://info.arxiv.org/help/moderation/index.html#submission-rate).

3. **Category.** Recommendation: `cs.CL` primary and `cs.LG` cross-list, based on the paper's controlled language-model behavior and mechanism investigation. This is a recommendation, not a PI decision or guaranteed moderator classification. Consider `cs.AI` only if the PI prefers the general artificial-cognition framing. See [category definitions](https://arxiv.org/category_taxonomy) and [cross-list guidance](https://info.arxiv.org/help/cross.html).

4. **License.** No final selection is recorded. With no target journal or funder license requirement recorded, the arXiv perpetual, non-exclusive license is a reasonable first-preprint option; CC BY 4.0 is the alternative if broad reuse and adaptation with attribution are intended. The license for an announced version is irrevocable, even if a later version uses another license. The PI should select it after checking any applicable journal/funder requirements. See [official license guidance](https://info.arxiv.org/help/license/index.html).

5. **PI read-through and author information.** STATUS records the final read-through as pending. The AI statement already says the author has reviewed the paper and takes responsibility. Before submitting, that statement should match what the PI has completed, and the name, affiliation, email, and any acknowledgments should be checked. The present AI disclosure meets the documented disclosure structure; see [arXiv's AI policy](https://info.arxiv.org/help/moderation/index.html#policy-for-authors-use-of-generative-ai-language-tools).

6. **Server processing and final submission.** Upload the source archive, select `main.tex` and pdfLaTeX, and review arXiv's generated PDF. A TeX-produced manuscript should not be submitted as PDF alone. A successful local build cannot replace this final check. See [submission instructions](https://info.arxiv.org/help/submit/index.html). No cover letter, invented journal reference, or invented DOI has been prepared.

## Submission metadata and timing

`paper/arxiv_submission_metadata.txt` contains copyable title, author information, abstract, and Comments, with recommended category and license options clearly marked as undecided. It reflects the current manuscript; synchronize it after any approved abstract revision.

Suggested Comments: `35 pages, 6 figures. Code and protocols: https://github.com/BeibaiDraco/mind-connecting`

Leave journal reference, external publication DOI, and institutional report number blank unless applicable. The draft's September 2026 date is fixed, not generated with `\today`; changing it to the eventual submission month is optional.

The normal cutoff is 14:00 US Eastern (13:00 Chicago); scheduled announcements are at 20:00 Eastern (19:00 Chicago), Sunday through Thursday. Quality checks commonly take one to four days and can take longer. October 12 is explicitly listed as a 2026 holiday. An arXiv identifier is assigned at announcement, not at upload. See the [official availability schedule](https://info.arxiv.org/help/availability.html); do not promise a same-day announcement.

## Historical notes and scope

`paper/writing_notes.md` and some STATUS navigation/audit bullets contain superseded statements: an earlier page count, 47 citations, the old Figure 1d wording, provisional author metadata, v3 not frozen, or T3 still to be run. Current manuscript, results, and decision-log entries supersede these. They are not evidence that experiments or author fields are missing.

Raw records and the original frozen-history bundle are not publicly downloadable from the repository. The current manuscript discloses this correctly. Public release would improve reproducibility, but the reviewed general arXiv instructions do not make it a universal prerequisite for this submission. The PI's first-version plan already leaves the second model for later.

Only packaging and audit documentation were changed. No manuscript, figures, frozen protocols, research metrics, or experimental results were modified; no new research decision was appended to the decision log.
