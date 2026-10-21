# Prior uses and closest precedents: mind-connecting

Assessed 2026-10-20, Chicago. Targeted primary-source search, not a systematic review or a priority certification. Prepared using the maiwen:prior-use workflow. No new collection, research freeze or manuscript change.

## Corpus identity and existing use

This project's generated episode corpus is called mind-connecting, mind-bridging, and V1–V6 in its internal documents. These labels denote different studies, not interchangeable datasets. The collection purpose is to test content access and source attribution between separately initialized instances of a frozen language model, later extended to persistent actual-action interaction. Episode is the statistical unit.

The preserved manuscript is *Mine or Yours? Mind-Bridged Language Models Take Each Other's Memories as Their Own*, September 2026, in `paper/`. Its principal results are Qwen memory-link studies; it also reports earlier online hidden-state studies. Completed Llama replication and V5 source-conflict/STATIC evidence are assessed in [the post-collection story](../../docs/paper/post_collection_story_20261012.md). V6 includes engineering observations and small Qwen development experiments; the intended full formal interaction study has not started. These are owner-reported uses of the project's observations. No independent external reuse was established by this search. External papers below use different observations and are related work, not reanalyses of this corpus. This review does not verify the project's external publication status.

## Primary-source map

| Source and reading scope | Scientific object, measurement and comparison | Consequence for this project |
|---|---|---|
| Ramesh & Li, [Communicating Activations Between Language Model Agents](https://proceedings.mlr.press/v267/ramesh25a.html), ICML 2025. Proceedings metadata and [v1 methods/coordination results, §3–4.1](https://arxiv.org/html/2501.14082v1) inspected; final PDF not compared line by line. | Combines intermediate model activations; tests private-information signaling games and reasoning performance against communication alternatives. | Direct activation communication and a private-information decision task are established precedents. Simply demonstrating either cannot carry a first-study claim. The inspected games do not supply our proposed persistent self/other causal-attribution test. |
| Zou et al., [Latent Collaboration in Multi-Agent Systems](https://arxiv.org/html/2511.20639v1), 2025 preprint version. §2–3 and reported evaluation read. | Latent generation with shared layerwise KV working memory; sequential/hierarchical agents evaluated on accuracy and inference efficiency. | Latent collaboration itself is established. A new method must add a finding or functional capability beyond another cache exchange. This version's tested organization is not evidence about our private-goal attribution question. |
| Shi et al., [KVComm: Enabling Efficient LLM Communication through Selective KV Sharing](https://arxiv.org/html/2510.03346v1). §2–3.1 and reported results inspected. | Sender prefills context; selected layers' KV pairs inform a receiver query. Contrasts information carriers, layer selection and efficiency. | The cache medium and importance of connection placement are precedents. Distinct from Ye et al.'s similarly named [KVCOMM](https://arxiv.org/abs/2510.12872), whose abstract addresses prefilling/cache-offset reuse; that latter work was not read in full here. |
| Ackerman & Panickssery, [Inspection and Control of Self-Generated-Text Recognition Ability in Llama3-8b-Instruct](https://arxiv.org/html/2410.02064v1), 2024 version. Methods, §3.2 and discussion inspected. | Extracts an authorship-related residual direction; addition, projection and input-time intervention alter self-authorship judgments. Includes specificity controls. | Neither changing self-reports through a vector nor layer-dependent self-attribution effects are new by themselves. Their task concerns authorship recognition; ours has known private assignment records and content-bearing donor memory. That difference needs evidence, not merely new terminology. |
| Zhang & Emu, [Do Latent Channels Actually Communicate?](https://arxiv.org/html/2607.26773), 2026. Framework, results and conclusion inspected. | Replaces messages with other-example, receiver-generated or absent messages; separates prediction sensitivity, example-specific task value and separate-agent value. | Showing an activation changes answers, or auditing content against generic perturbation, is already studied. Our paper must specify the additional source/control endpoint. |
| Cheng et al., [When Does Latent Communication Pay?](https://arxiv.org/html/2608.04893v2), 2026. Abstract, audit design/scope, limitations and Appendix C.2 inspected. | Audits intact, mismatched, zero and random cache relays under different receiver-information needs. Includes donor-consistent answers under mismatched caches. | Particularly close to a generic donor-following interpretation of our work. The remaining distinction is original-source attribution with known conflicting records, access contrasts and readout-time intervention, not the bare fact that recipients follow donor content. |
| Liang et al., [When KV Cache Reuse Fails in Multi-Agent Systems](https://aclanthology.org/2026.acl-long.327/), ACL 2026. Abstract and venue record only. | Abstract reports judge-choice inconsistency despite apparently stable task accuracy, linked to cross-candidate attention. | A relevant warning that cache-induced behavioral changes need mechanism-specific evaluation. Full methods remain unread; not used to assert an uncovered self/other gap. |

## Search record and consequential limits

Search date: 2026-10-20. Sources: web search and original arXiv HTML, PMLR proceedings, ACL Anthology; local bibliography supplied additional leads. Queries included:

- `LLM mind melding brain bridging self other attribution KV cache ownership`
- `LatentMAS latent collaboration multi agent systems language models`
- `KVComm online cross context KV cache communication language model agents`
- `large language models self authorship activation steering self recognition vector`
- `"mind-bridged" "language"`, `"KVComm" "self" attribution`, `"latent communication" "source attribution"`
- `"latent communication" "self" "attribution"`; `"language models" "self-other" "cache"`; `"coupled" "language models" "agency" "latent"` with arXiv/ACL/OpenReview domain restrictions.
- `"self-other" "latent" LLM attribution memory` restricted to arXiv.

Literal self/other searches often returned irrelevant proceedings indexes or no results. That is weak retrieval, not evidence of absence. No complete forward-citation graph was traversed. A broad-search secondary lead titled *Learning to Communicate: Toward End-to-End Optimization of Multi-Agent Language Systems* with identifier 2604.21794 was not corroborated by the exact primary-domain search; it remains unverified and is not cited as an established result. Full screening of recent trained latent-communication systems remains a useful next search if the proposed functional-coupling study is developed. Method revisions after the inspected versions also need checking before manuscript priority language.

No reviewed source was identified as testing exactly our combination of known original records, access-versus-attribution contrasts, conflicting third-party records and same-state link removal. This is **not found within these searches**, not a claim that nobody has done it. The proposed persistent reciprocal-control/self-attribution combination likewise remains a candidate gap rather than an established first.

## Disposition

Existing corpus: a worthwhile bounded empirical source-attribution paper is supportable in my assessment, provided the revised manuscript integrates counterevidence and distinguishes matched from unmatched comparisons. Novelty is moderate/uncertain relative to the closest audits; publication or top-conference acceptance is not established by this judgment.

Stronger brain-bridge-inspired question: not answered by current evidence. Additional experiments must add a causal result about selective use, control or attribution under a specified connection, rather than merely another latent carrier or a larger donor-following rate. See the [candidate comparison and evidence ladder](precedents/internal_coupling_self_other.md). No new experiment is adopted by this assessment.
