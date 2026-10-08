"""Real, pinned Llama engineering acceptance; never a research-data stage.

Use scripts/check_llama_acceptance.py on the GPU host after downloading the
authorized assets. This module must not use the legacy Qwen GPU fixture.
Same-shape no-link, causal, and isolation invariants require bitwise equality.
Only different-shape BF16 forwards allow max absolute logit error <= 0.25 and
mean error <= 0.025; confident top-1 choices must agree (reference margin > 0.5).
These tolerances are fixed before execution and must not be relaxed after a fail.
"""

from __future__ import annotations

import json
import math
from contextlib import contextmanager

import pytest

torch = pytest.importorskip("torch")
pytestmark = [pytest.mark.gpu,
              pytest.mark.skipif(not torch.cuda.is_available(), reason="needs a CUDA GPU")]

from mb import chat, tasks  # noqa: E402
from mb.bridge import BridgeHook, LayerCalibration  # noqa: E402
from mb.conditions import ArmConfig  # noqa: E402
from mb.model_profiles import LLAMA31  # noqa: E402
from mb.run import snapshot_hash  # noqa: E402
from mb.runtime import Engine, KVPlan, load_model, make_plan, select_rows  # noqa: E402

LAYER = 21
MAX_LOGIT_ERROR = 0.25
MEAN_LOGIT_ERROR = 0.025


def _arm(condition: str = "C0", **kwargs) -> ArmConfig:
    return ArmConfig(condition, layer=LAYER, model_profile=LLAMA31.key, **kwargs)


def _plan(engine: Engine, arm: ArmConfig, rows: int):
    return make_plan(arm, ["A", "B"] * (rows // 2), [None] * rows,
                     engine.cal, engine.device, d=engine.d)


def _kv(engine: Engine, rows: int, weight: float = 1.0, scope: str = "P") -> KVPlan:
    return KVPlan(torch.arange(rows, device=engine.device) % 2 == 0,
                  math.log(weight) if weight else -math.inf, scope)


def _clone(engine: Engine, state):
    return select_rows(state, list(range(state.rows)), engine.model.config)


@contextmanager
def _unhooked(engine: Engine):
    engine.hook.remove()
    try:
        yield
    finally:
        engine.hook = BridgeHook(engine.model.model.layers[LAYER - 1], LAYER)


def _logit_comparison(actual, reference, record_property, label: str) -> None:
    assert torch.isfinite(actual).all() and torch.isfinite(reference).all()
    error = (actual.float() - reference.float()).abs()
    maximum, mean = float(error.max()), float(error.mean())
    agreement = float((actual.argmax(-1) == reference.argmax(-1)).float().mean())
    top = reference.float().topk(2, dim=-1).values
    margin = top[..., 0] - top[..., 1]
    record_property(label, json.dumps({"max_abs_error": maximum, "mean_abs_error": mean,
                                      "top1_agreement": agreement,
                                      "min_top2_margin": float(margin.min())}))
    assert maximum <= MAX_LOGIT_ERROR, f"{label}: max logit error {maximum}"
    assert mean <= MEAN_LOGIT_ERROR, f"{label}: mean logit error {mean}"
    confident = margin > 2 * MAX_LOGIT_ERROR
    assert torch.equal(actual.argmax(-1)[confident], reference.argmax(-1)[confident])


@pytest.fixture(scope="module")
def llama():
    import tokenizers
    import transformers

    assert transformers.__version__ == "4.57.1"
    assert tokenizers.__version__ == "0.22.1"
    assert torch.cuda.is_bf16_supported(), "acceptance requires native BF16 support"
    tok = chat.load_tokenizer(profile=LLAMA31)
    model = load_model(profile=LLAMA31, tokenizer=tok)
    assert next(model.parameters()).dtype == torch.bfloat16
    # Synthetic normalization tests mechanics only and is never saved for science runs.
    cal = LayerCalibration(LAYER, torch.zeros(LLAMA31.hidden_size),
                           torch.ones(LLAMA31.hidden_size), 1.0)
    engine = Engine(model, tok, LAYER, cal)
    episodes = tasks.make_episodes(2, "v4-llama-engineering-acceptance", seed=0)
    private = [tasks.private_prefix_ids(tok, ep, role) for ep in episodes for role in tasks.ROLES]
    notes = engine.generate_notes(private)
    prefixes = [[*prefix, *note, *chat.close(tok), *tasks.reflection_turn_ids(tok)]
                for prefix, note in zip(private, notes)]
    try:
        yield {"tok": tok, "model": model, "engine": engine, "episodes": episodes,
               "prefixes": prefixes, "notes": notes}
    finally:
        engine.close()


def test_native_stop_set_finite_logits_and_task_labels(llama, record_property):
    engine, tok = llama["engine"], llama["tok"]
    spec = chat.runtime_tokens(tok)
    generation = json.loads((LLAMA31.tokenizer_dir / "generation_config.json").read_text())
    assert set(spec.eos_ids) == set(generation["eos_token_id"]) == {128001, 128008, 128009}
    assert set(engine.model.generation_config.eos_token_id) == set(spec.eos_ids)
    assert all(len(note) <= tasks.NOTE_MAX_TOKENS and not set(note) & set(spec.eos_ids)
               for note in llama["notes"])
    state = engine.prefill(llama["prefixes"])
    assert torch.isfinite(state.logits).all() and torch.isfinite(state.ema).all()
    assert state.mailbox.dtype == torch.bfloat16 and state.ema.dtype == torch.float32
    assert not torch.isin(state.pending, engine.eos).any()
    assert all(seq[0] == spec.bos_id and seq.count(spec.bos_id) == 1 for seq in llama["prefixes"])
    forced = torch.zeros(len(spec.eos_ids), LLAMA31.vocab_size, device=engine.device)
    forced[:, spec.label_ids[0]] = 1
    for i, stop in enumerate(spec.eos_ids):
        forced[i, stop] = 100
    original = forced.clone()
    assert bool((engine.no_eos_argmax(forced) == spec.label_ids[0]).all())
    assert torch.equal(forced, original), "EOS masking modified original logits"
    for ep in llama["episodes"]:
        for role in tasks.ROLES:
            for question in tasks.readout_questions(tok, ep, role, rotations=[0, 2]):
                text = tok.decode(question.suffix_ids, clean_up_tokenization_spaces=False)
                for label, token in zip(chat.LABELS, spec.label_ids):
                    assert chat.encode(tok, text + label) == [*question.suffix_ids, token]
    record_property("eos_ids", json.dumps(spec.eos_ids))
    record_property("note_lengths", json.dumps([len(note) for note in llama["notes"]]))


def test_no_link_matches_unhooked_cached_generation(llama, record_property):
    from transformers import DynamicCache

    engine, model = llama["engine"], llama["model"]
    state = engine.prefill(llama["prefixes"])
    engine.run_reflection(state, _plan(engine, _arm(), state.rows), ticks=8)
    path = state.consumed_matrix()
    rows, width = len(llama["prefixes"]), max(map(len, llama["prefixes"]))
    ids = torch.full((rows, width), engine.pad_id, dtype=torch.long, device=engine.device)
    mask = torch.zeros_like(ids)
    for row, prefix in enumerate(llama["prefixes"]):
        ids[row, -len(prefix):] = torch.tensor(prefix, device=engine.device)
        mask[row, -len(prefix):] = 1
    positions = (mask.cumsum(-1) - 1).clamp(min=0)
    cache = DynamicCache(config=model.config)
    chosen = []
    with _unhooked(engine), torch.no_grad():
        out = model.model(input_ids=ids, attention_mask=mask, position_ids=positions,
                          past_key_values=cache, use_cache=True)
        logits = model.lm_head(out.last_hidden_state[:, -1]).float()
        next_pos = positions[:, -1] + 1
        for tick in range(path.shape[1]):
            chosen.append(engine.no_eos_argmax(logits))
            mask = torch.cat([mask, torch.ones(rows, 1, dtype=mask.dtype, device=engine.device)], 1)
            out = model.model(input_ids=path[:, tick:tick + 1], attention_mask=mask,
                              position_ids=next_pos[:, None], past_key_values=cache, use_cache=True)
            logits = model.lm_head(out.last_hidden_state[:, -1]).float()
            next_pos += 1
    assert torch.equal(torch.stack(chosen, 1), path), "unhooked free greedy path differs"
    assert torch.equal(logits, state.logits), "read-only hooks changed the no-link logits"
    assert torch.isfinite(logits).all()
    record_property("no_link_greedy_agreement", 1.0)
    record_property("no_link_max_abs_error", float((logits - state.logits).abs().max()))


def test_inactive_attention_and_zero_weight_are_exact(llama):
    engine, model = llama["engine"], llama["model"]
    outputs = []
    try:
        for implementation in ("sdpa", "mb_kv"):
            model.config._attn_implementation = implementation
            state = engine.prefill(llama["prefixes"])
            logits, _, _ = engine.step(state, state.pending, None)
            outputs.append((state.logits.clone(), logits))
    finally:
        model.config._attn_implementation = "mb_kv"
    assert all(torch.equal(a, b) for a, b in zip(*outputs))
    baseline = engine.prefill(llama["prefixes"])
    plain, zero = _clone(engine, baseline), _clone(engine, baseline)
    left, _, _ = engine.step(plain, plain.pending, None)
    right, _, _ = engine.step(zero, zero.pending, None, kv=_kv(engine, zero.rows, weight=0))
    assert torch.equal(left, right)
    assert bool((engine.last_kv_mass[0::2] == 0).all())
    assert bool(engine.last_kv_mass[1::2].isnan().all())
    assert snapshot_hash(plain) == snapshot_hash(zero)
    linked = _clone(engine, baseline)
    linked_logits, _, _ = engine.step(linked, linked.pending, None, kv=_kv(engine, linked.rows))
    assert torch.equal(left[1::2], linked_logits[1::2]), "reading changed donor logits"
    for plain_layer, linked_layer in zip(plain.cache.layers, linked.cache.layers):
        assert torch.equal(plain_layer.keys[1::2], linked_layer.keys[1::2])
        assert torch.equal(plain_layer.values[1::2], linked_layer.values[1::2])


def test_one_way_isolation_and_previous_tick_visibility(llama):
    engine = llama["engine"]
    base = engine.prefill(llama["prefixes"])
    kv = _kv(engine, base.rows, scope="ALL")
    first, changed = _clone(engine, base), _clone(engine, base)
    altered = changed.pending.clone()
    altered[1::2] = (altered[1::2] + 7) % 1000 + 100
    original_logits, _, _ = engine.step(first, first.pending, None, kv=kv)
    changed_logits, _, _ = engine.step(changed, altered, None, kv=kv)
    assert torch.equal(original_logits[0::2], changed_logits[0::2]), "same-tick donor leak"
    forced = engine.no_eos_argmax(original_logits)
    later, _, _ = engine.step(first, forced, None, kv=kv)
    later_changed, _, _ = engine.step(changed, forced, None, kv=kv)
    assert not torch.equal(later[0::2], later_changed[0::2]), "committed donor change was invisible"
    first, changed = _clone(engine, base), _clone(engine, base)
    altered = changed.pending.clone()
    altered[0::2] = (altered[0::2] + 7) % 1000 + 100
    original_logits, _, _ = engine.step(first, first.pending, None, kv=kv)
    changed_logits, _, _ = engine.step(changed, altered, None, kv=kv)
    assert torch.equal(original_logits[1::2], changed_logits[1::2])
    forced = engine.no_eos_argmax(original_logits)
    later, _, _ = engine.step(first, forced, None, kv=kv)
    later_changed, _, _ = engine.step(changed, forced, None, kv=kv)
    assert torch.equal(later[1::2], later_changed[1::2]), "donor read recipient in ONE"
    for a, b in zip(first.cache.layers, changed.cache.layers):
        assert torch.equal(a.keys[1::2], b.keys[1::2])
        assert torch.equal(a.values[1::2], b.values[1::2])
    assert bool(((engine.last_kv_mass[0::2] > 0) & (engine.last_kv_mass[0::2] < 1)).all())


def test_padding_positions_cache_and_causal_prefix(llama, record_property):
    engine, tok, model = llama["engine"], llama["tok"], llama["model"]
    short = chat.native_conversation(tok, [{"role": "user", "content": "Remember the blue record."}],
                                     add_generation_prompt=True)
    long = chat.native_conversation(tok, [{"role": "user", "content": "Keep these records separate. " * 9}],
                                    add_generation_prompt=True)
    assert len(long) > len(short)
    pair = engine.prefill([long, short])
    single = engine.prefill([short])
    assert pair.next_pos.tolist() == [len(long), len(short)]
    assert not pair.attn[1, :len(long) - len(short)].any()
    _logit_comparison(pair.logits[1:], single.logits, record_property, "left_padded_prefill")
    forced = chat.runtime_tokens(tok).label_ids[0]
    for _ in range(3):
        batch_logits, _, _ = engine.step(pair, torch.full_like(pair.pending, forced), None)
        single_logits, _, _ = engine.step(single, torch.full_like(single.pending, forced), None)
    _logit_comparison(batch_logits[1:], single_logits, record_property, "left_padded_cached_ticks")
    assert pair.next_pos.tolist() == [len(long) + 3, len(short) + 3]
    assert bool((pair.attn[:, -3:] == 1).all()), "padding inserted during single-token ticks"
    assert all(layer.keys.shape[-2] == len(long) + 3 for layer in pair.cache.layers)
    rebuilt = engine.prefill([short + [forced] * 3])
    _logit_comparison(single_logits, rebuilt.logits, record_property, "cache_vs_full_prefill")
    # Same batch/length: a changed future token cannot change any earlier hidden state.
    sequence = torch.tensor([short, short], dtype=torch.long, device=engine.device)
    sequence[1, -1] = forced
    with _unhooked(engine), torch.no_grad():
        output = model.model(input_ids=sequence, attention_mask=torch.ones_like(sequence),
                             position_ids=torch.arange(sequence.shape[1], device=engine.device)[None].expand(2, -1),
                             use_cache=False).last_hidden_state
    assert torch.isfinite(output).all()
    assert torch.equal(output[0, :-1], output[1, :-1]), "causal mask permits future input"


def test_partner_padding_and_scope_boundaries(llama):
    engine, tok = llama["engine"], llama["tok"]
    short = chat.native_conversation(tok, [{"role": "user", "content": "Blue record."}],
                                     add_generation_prompt=True)
    long = chat.native_conversation(tok, [{"role": "user", "content": "Separate records. " * 9}],
                                    add_generation_prompt=True)
    base = engine.prefill([long, short])
    clean, poisoned = _clone(engine, base), _clone(engine, base)
    pad_count = len(long) - len(short)
    assert pad_count > 0
    for layer in poisoned.cache.layers:
        layer.keys[1, :, :pad_count] += 50
        layer.values[1, :, :pad_count] += 50
    left, _, _ = engine.step(clean, clean.pending, None, kv=_kv(engine, 2))
    right, _, _ = engine.step(poisoned, poisoned.pending, None, kv=_kv(engine, 2))
    assert torch.equal(left, right), "masked donor padding affected computation"
    first, changed = _clone(engine, base), _clone(engine, base)
    altered = changed.pending.clone()
    altered[1] = (altered[1] + 7) % 1000 + 100
    left, _, _ = engine.step(first, first.pending, None, kv=_kv(engine, 2))
    right, _, _ = engine.step(changed, altered, None, kv=_kv(engine, 2))
    assert torch.equal(left[0], right[0])
    forced = engine.no_eos_argmax(left)
    left, _, _ = engine.step(first, forced, None, kv=_kv(engine, 2))
    right, _, _ = engine.step(changed, forced, None, kv=_kv(engine, 2))
    assert torch.equal(left[0], right[0]), "KV-P read a donor C token"
    assert float(engine.last_kv_mass_cr[0]) == 0
    state = _clone(engine, base)
    logits, _, _ = engine.step(state, state.pending, None, kv=_kv(engine, 2, scope="C"))
    assert float(engine.last_kv_mass[0]) == 0, "C scope read prefix keys"
    engine.step(state, engine.no_eos_argmax(logits), None, kv=_kv(engine, 2, scope="C"))
    assert float(engine.last_kv_mass[0]) > 0, "C scope never read the committed C token"


def test_bf16_snapshot_clone_and_continuation(llama, record_property):
    engine = llama["engine"]
    arm = _arm("ONE", interface="kv", kv_scope="P", gain=1)
    state = engine.prefill(llama["prefixes"])
    plan = _plan(engine, arm, state.rows)
    engine.run_reflection(state, plan, ticks=4)
    before = snapshot_hash(state)
    snap = _clone(engine, state)
    assert snapshot_hash(snap) == before
    assert all(layer.keys.dtype == torch.bfloat16 and layer.values.dtype == torch.bfloat16
               for layer in state.cache.layers)
    altered = _clone(engine, state)
    altered.cache.layers[0].values[0, 0, 0, 0] += 1
    assert snapshot_hash(altered) != before, "BF16 cache mutation escaped the fingerprint"
    assert snapshot_hash(state) == before
    engine.run_reflection(state, plan, ticks=3)
    resumed = _clone(engine, snap)
    engine.run_reflection(resumed, plan, ticks=3)
    assert snapshot_hash(state) == snapshot_hash(resumed), "restored continuation diverged"
    assert snapshot_hash(snap) == before
    record_property("bf16_snapshot_sha256", before)


def test_c48_full_rf_fork_isolation(llama, monkeypatch, record_property):
    engine, tok = llama["engine"], llama["tok"]
    full = _arm("ONE", interface="kv", kv_scope="P", gain=1)
    rf = _arm("ONE", interface="kv", kv_scope="P", gain=1, readout_mode="RF")
    state = engine.prefill(llama["prefixes"])
    engine.run_reflection(state, _plan(engine, full, state.rows), ticks=tasks.REFLECTION_TICKS)
    before = snapshot_hash(state)
    branches = [(0, "A"), (1, "A")]
    questions = [tasks.make_question(tok, ep, "A", "START", 0) for ep in llama["episodes"]]
    assert len({len(q.suffix_ids) for q in questions}) == 1
    suffixes = torch.tensor([list(q.suffix_ids) for q in questions])
    assert bool((suffixes[:, 0] == chat.close(tok)[0]).all())
    rf_states = []
    real_step = engine.step

    def record_rf(branch, tokens, injection, kv=None):
        assert branch.rows == len(branches) and injection is None and kv is None
        if not rf_states:
            rf_states.append((branch, branch.ema.clone(), branch.mailbox.clone()))
        return real_step(branch, tokens, injection, kv=kv)

    with monkeypatch.context() as scoped:
        scoped.setattr(engine, "step", record_rf)
        cut = engine.run_readout(state, branches, suffixes, rf, [None, None])
    branch, ema_before, mailbox_before = rf_states[0]
    assert torch.equal(branch.ema, ema_before) and torch.equal(branch.mailbox, mailbox_before)
    assert snapshot_hash(state) == before, "RF mutated its shared C48 source"
    kept = engine.run_readout(state, branches, suffixes, full, [None, None], generate=4)
    assert snapshot_hash(state) == before, "FULL mutated its shared C48 source"
    assert torch.equal(kept["r_donor_tokens"][:, 0], state.pending[1::2])
    assert bool((kept["r_kv_mass"] > 0).all())
    assert bool((kept["r_kv_mass_cr_mean"] == 0).all())
    assert not torch.isin(kept["generated"], engine.eos).any()
    repeated = engine.run_readout(state, branches, suffixes, rf, [None, None])
    reversed_full = engine.run_readout(state, branches[::-1], suffixes.flip(0), full, [None, None])
    assert snapshot_hash(state) == before
    for key in ("label_logits", "label_logprobs", "label_mass"):
        assert torch.isfinite(kept[key]).all() and torch.isfinite(cut[key]).all()
        assert torch.equal(cut[key], repeated[key]), "FULL contaminated a later RF branch"
        assert torch.equal(kept[key], reversed_full[key].flip(0)), "branch-order dependence"
    assert kept["label_logits"].dtype == torch.float32
    assert torch.allclose(kept["label_mass"], kept["label_logprobs"].exp().sum(-1), atol=1e-6)
    assert bool(((kept["label_mass"] >= 0) & (kept["label_mass"] <= 1 + 1e-6)).all())
    record_property("shared_c48_sha256", before)
    record_property("readout_suffix_tokens", int(suffixes.shape[1]))
    record_property("minimum_label_mass", float(kept["label_mass"].min()))
