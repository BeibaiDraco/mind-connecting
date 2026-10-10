# V5 Qwen guarded continuation

Reviewed on 2026-10-09 (Chicago).

The same instance was restored for the independent Qwen branch. The initial
recovery protection check stopped before any provider start: two clock reads
made its nominal 600-second commissioning window 92 microseconds too long for
its strict bound. The failed helper, intent and receipt were preserved. A new
private helper captures one timestamp for both fields and uses a fresh control
directory; 13 focused tests and an independent review passed, including an
advancing-clock regression through the real guard validator. Scientific source,
protocols and numerical gates were not changed.

The corrected recovery armed a detached short guard before the single provider
start request. The existing full local guard stayed live. A new remote guard
uses the exact original full budget and deadline, with byte-identical historical
short-guard retirement receipts. The short recovery guard was acknowledged only
after fresh remote proof and a live Qwen stage child were verified. The provider
quote remains USD 1.12/hour; the conservative budget uses USD 1.40/hour.

The reviewed Qwen controller started baseline run
`20261010-013326_v5_qwen_provenance_base_v5_qwen_provenance_base`. Its fixed
baseline/validity/formal sequence remains conditional on frozen gates and exact
SD backup verification. Its stage estimates reserve the full remaining bounded
STATIC package and overhead. The retained padded remaining forecast is 23.76
hours and cumulative cost approximately USD 38.36 at preparation, including all
elapsed time and reserves. STATIC still needs measured timing before expensive
stages. No formal Qwen collection was claimed at controller launch.

The complete Llama controller archive was also downloaded and SHA256-verified:
`70331c63f666e4ae69c4da08d40f26583a4a14554a8524ff7d3ca4e646f43598`.
Its final stage receipt confirms completed failed validity with verified backup;
no formal intent or formal freeze exists.

At 01:34 UTC the Qwen baseline had 132 successful reads, no malformed lines and
a live model child/controller. It is still a prerequisite stage, not formal
N600 collection. The full offline suite passed (361 passed, 5 skipped).
