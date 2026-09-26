"""Runtime correctness on the real model (protocol v0.5 §11.1-9). Run on the GPU machine:

    pytest -m gpu -q

These tests guard the causal interpretation: zero-gain equivalence, direction, delay,
snapshot/branch independence, hook formats, EOS handling.
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")
pytestmark = [pytest.mark.gpu,
              pytest.mark.skipif(not torch.cuda.is_available(), reason="needs a CUDA GPU")]

from mb import chat, tasks  # noqa: E402
from mb.bridge import LayerCalibration  # noqa: E402
from mb.conditions import ArmConfig  # noqa: E402

LAYER = 18


@pytest.fixture(scope="module")
def setup():
    from mb.runtime import Engine, load_model

    tok = chat.load_tokenizer()
    model = load_model()
    d = model.config.hidden_size
    # A synthetic calibration is enough for mechanics; real runs use the calibration stage.
    cal = LayerCalibration(LAYER, torch.zeros(d), torch.ones(d), 1.0)
    engine = Engine(model, tok, LAYER, cal)
    eps = tasks.make_episodes(3, "dev", seed=11)
    notes = engine.generate_notes([tasks.private_prefix_ids(tok, e, r) for e in eps for r in tasks.ROLES])
    prefixes = []
    for i, e in enumerate(eps):
        for j, r in enumerate(tasks.ROLES):
            ids = [*tasks.private_prefix_ids(tok, e, r), *notes[2 * i + j], *chat.close(tok),
                   *tasks.reflection_turn_ids(tok)]
            prefixes.append(ids)
    yield {"tok": tok, "model": model, "engine": engine, "eps": eps, "prefixes": prefixes, "cal": cal}
    engine.close()


def _plan(setup, arm, rows):
    from mb.runtime import make_plan

    e = setup["engine"]
    return make_plan(arm, ["A", "B"] * (rows // 2), [None] * rows, e.cal, e.device, d=e.d)


def test_prefill_capture_and_notes(setup):
    state = setup["engine"].prefill(setup["prefixes"])
    assert state.mailbox.shape == (len(setup["prefixes"]), setup["engine"].d)
    assert not torch.isin(state.pending, setup["engine"].eos).any()


def test_zero_gain_equals_plain_forward(setup):
    """Bridge code present with no writes == the unhooked model on the same token path."""
    from transformers import DynamicCache

    engine, model = setup["engine"], setup["model"]
    state = engine.prefill(setup["prefixes"])
    engine.run_reflection(state, _plan(setup, ArmConfig("C0"), state.rows), ticks=12)
    path = state.consumed_matrix()
    engine.hook.remove()
    try:
        rows, length = len(setup["prefixes"]), max(len(p) for p in setup["prefixes"])
        ids = torch.full((rows, length), chat.ENDOFTEXT, dtype=torch.long, device=engine.device)
        attn = torch.zeros(rows, length, dtype=torch.long, device=engine.device)
        for i, p in enumerate(setup["prefixes"]):
            ids[i, length - len(p):] = torch.tensor(p, device=engine.device)
            attn[i, length - len(p):] = 1
        pos = (attn.cumsum(-1) - 1).clamp(min=0)
        cache = DynamicCache(config=model.config)
        with torch.no_grad():
            out = model(input_ids=ids, attention_mask=attn, position_ids=pos, past_key_values=cache, use_cache=True)
            nxt = pos[:, -1] + 1
            ref_tokens = []
            logits = out.logits[:, -1, :].float()
            for t in range(path.shape[1]):
                masked = logits.clone()
                masked[:, list(chat.EOS_IDS)] = -float("inf")
                ref_tokens.append(masked.argmax(-1))
                attn = torch.cat([attn, torch.ones(rows, 1, dtype=torch.long, device=engine.device)], 1)
                out = model(input_ids=path[:, t:t + 1], attention_mask=attn, position_ids=nxt[:, None],
                            past_key_values=cache, use_cache=True)
                nxt = nxt + 1
                logits = out.logits[:, -1, :].float()
        assert torch.equal(torch.stack(ref_tokens, 1), path), "greedy path diverged with zero gain"
        assert torch.allclose(logits, state.logits, atol=1e-2, rtol=0)
    finally:
        from mb.bridge import BridgeHook
        engine.hook = BridgeHook(model.model.layers[LAYER - 1], LAYER)


def test_direction_and_delay(setup):
    """ONE: A reacts to B's message one tick later; B never reacts to A."""
    from mb.runtime import select_rows

    engine = setup["engine"]
    base = engine.prefill(setup["prefixes"])
    arm = ArmConfig("ONE", gain=2.0)
    plan = _plan(setup, arm, base.rows)
    a = select_rows(base, list(range(base.rows)), setup["model"].config)
    b = select_rows(base, list(range(base.rows)), setup["model"].config)
    # Perturb only B's mailbox in copy b; A in copy b should differ from copy a at this tick.
    b.mailbox[1::2] += 50.0
    la, _, _ = engine.step(a, a.pending, engine.injection(a, plan))
    lb, _, _ = engine.step(b, b.pending, engine.injection(b, plan))
    assert not torch.allclose(la[0::2], lb[0::2]), "A did not receive B's message"
    assert torch.allclose(la[1::2], lb[1::2]), "B reacted to its own mailbox perturbation"
    # Delay: a perturbation of B's *token* at tick t reaches A only at t+1.
    c = select_rows(base, list(range(base.rows)), setup["model"].config)
    d = select_rows(base, list(range(base.rows)), setup["model"].config)
    tok_c, tok_d = c.pending.clone(), d.pending.clone()
    tok_d[1::2] = (tok_d[1::2] + 7) % 1000 + 100
    lc, _, zc = engine.step(c, tok_c, engine.injection(c, plan))
    ld, _, zd = engine.step(d, tok_d, engine.injection(d, plan))
    assert torch.allclose(lc[0::2], ld[0::2]), "A saw B's same-tick token"
    engine.advance(c, lc, zc, 1, True)
    engine.advance(d, ld, zd, 1, True)
    lc2, _, _ = engine.step(c, c.pending, engine.injection(c, plan))
    ld2, _, _ = engine.step(d, c.pending, engine.injection(d, plan))
    assert not torch.allclose(lc2[0::2], ld2[0::2]), "B's change never reached A"


def test_snapshot_continuation_and_branch_isolation(setup):
    from mb.runtime import select_rows

    engine, cfg = setup["engine"], setup["model"].config
    state = engine.prefill(setup["prefixes"])
    arm = ArmConfig("TWO", gain=0.5, form="ema")
    plan = _plan(setup, arm, state.rows)
    engine.run_reflection(state, plan, ticks=6)
    snap = select_rows(state, list(range(state.rows)), cfg)
    checksum = [k.float().sum().item() for k, _ in [(l.keys, l.values) for l in snap.cache.layers][:3]]
    engine.run_reflection(state, plan, ticks=4)
    branch = select_rows(snap, list(range(snap.rows)), cfg)
    engine.run_reflection(branch, plan, ticks=4)
    assert torch.equal(branch.consumed_matrix(), state.consumed_matrix())
    assert torch.allclose(branch.ema, state.ema, atol=1e-3)
    assert torch.allclose(branch.mailbox, state.mailbox, atol=1e-3)
    after = [k.float().sum().item() for k, _ in [(l.keys, l.values) for l in snap.cache.layers][:3]]
    assert checksum == after, "branch mutated the snapshot"


def test_readout_shapes_and_label_mass(setup):
    engine, tok = setup["engine"], setup["tok"]
    state = engine.prefill(setup["prefixes"])
    engine.run_reflection(state, _plan(setup, ArmConfig("C0"), state.rows), ticks=8)
    ep = setup["eps"][0]
    q = tasks.make_question(tok, ep, "A", "START", 0)
    out = engine.run_readout(state, [(0, "A")], torch.tensor([list(q.suffix_ids)]), ArmConfig("C0"), [None],
                             require_tick=8)
    assert out["label_logits"].shape == (1, 4)
    assert float(out["label_mass"][0]) > 0.5
    assert out["label_logits"].dtype == torch.float32
    assert torch.allclose(out["label_mass"], out["label_logprobs"].exp().sum(-1), atol=1e-6)
    assert bool((out["label_logprobs"] <= 0).all())


def test_readout_requires_the_c48_snapshot(setup):
    engine, tok = setup["engine"], setup["tok"]
    state = engine.prefill(setup["prefixes"])
    engine.run_reflection(state, _plan(setup, ArmConfig("C0"), state.rows), ticks=3)
    q = tasks.make_question(tok, setup["eps"][0], "A", "START", 0)
    with pytest.raises(RuntimeError, match="snapshot"):
        engine.run_readout(state, [(0, "A")], torch.tensor([list(q.suffix_ids)]), ArmConfig("C0"), [None])


def test_mailbox_is_bf16_message_of_fp32_ema(setup):
    """Review I1: m = BF16(N(e)) is stored; e stays fp32."""
    from mb.bridge import message

    engine = setup["engine"]
    state = engine.prefill(setup["prefixes"])
    engine.run_reflection(state, _plan(setup, ArmConfig("TWO", gain=0.3, form="ema"), state.rows), ticks=3)
    assert state.mailbox.dtype == torch.bfloat16 and state.ema.dtype == torch.float32
    assert torch.equal(state.mailbox, message(state.ema, engine.cal))


def test_u_open_generates_exactly_80_tokens_without_eos(setup):
    """Review I2: fixed-length generation, EOS masked, both for unbridged and bridged readouts."""
    engine, tok = setup["engine"], setup["tok"]
    q = tasks.make_question(tok, setup["eps"][0], "A", "U_OPEN", None)
    suffixes = torch.tensor([list(q.suffix_ids)] * 2)
    for arm in (ArmConfig("C0"), ArmConfig("ONE", gain=0.3)):
        state = engine.prefill(setup["prefixes"])
        engine.run_reflection(state, _plan(setup, arm, state.rows), ticks=4)
        out = engine.run_readout(state, [(0, "A"), (1, "A")], suffixes, arm, [None, None], generate=80,
                                 require_tick=4)
        assert out["generated"].shape == (2, 80)
        assert not torch.isin(out["generated"], engine.eos).any()
        if arm.bridged:
            assert int(out["g_unmatched_ticks"].sum()) == 0


def _state_fingerprint(state):
    kv = [(l.keys.clone(), l.values.clone()) for l in state.cache.layers]
    return (kv, state.pending.clone(), state.logits.clone(), state.mailbox.clone(), state.ema.clone(),
            state.attn.clone(), state.next_pos.clone(), state.consumed_matrix().clone(), state.tick)


def _same(a, b):
    kv_a, *rest_a = a
    kv_b, *rest_b = b
    for (ka, va), (kb, vb) in zip(kv_a, kv_b):
        if not (torch.equal(ka, kb) and torch.equal(va, vb)):
            return False
    return all((torch.equal(x, y) if isinstance(x, torch.Tensor) else x == y) for x, y in zip(rest_a, rest_b))


def test_full_readout_first_tick_and_snapshot_isolation(setup):
    """R tick 1: recipient consumes IM_END (the suffix start) while the donor consumes its pending
    C49; readouts on several branches never modify the C snapshot."""
    engine, tok = setup["engine"], setup["tok"]
    arm = ArmConfig("TWO", gain=0.5, recipients=("A", "B"))
    state = engine.prefill(setup["prefixes"])
    engine.run_reflection(state, _plan(setup, arm, state.rows), ticks=5)
    before = _state_fingerprint(state)
    ep = setup["eps"][0]
    qa = tasks.make_question(tok, ep, "A", "START", 0)
    qb = tasks.make_question(tok, ep, "B", "START", 0)
    assert qa.suffix_ids[0] == chat.IM_END
    out = engine.run_readout(state, [(0, "A"), (0, "B")], torch.tensor([list(qa.suffix_ids), list(qb.suffix_ids)]),
                             arm, [None, None], require_tick=5)
    assert torch.equal(out["r_donor_tokens"][:, 0].to(state.pending.device),
                       torch.stack([state.pending[1], state.pending[0]]))
    assert bool((out["r_inj_ratio"] > 0).all()) and int(out["r_unmatched"].sum()) == 0
    assert _same(before, _state_fingerprint(state)), "a readout branch mutated the snapshot"
    # Branch order does not change results.
    out2 = engine.run_readout(state, [(0, "B"), (0, "A")], torch.tensor([list(qb.suffix_ids), list(qa.suffix_ids)]),
                              arm, [None, None], require_tick=5)
    assert torch.allclose(out["label_logits"], out2["label_logits"].flip(0), atol=1e-3)


def test_rf_and_ro_modes(setup):
    engine, tok = setup["engine"], setup["tok"]
    q = tasks.make_question(tok, setup["eps"][0], "A", "START", 0)
    suffix = torch.tensor([list(q.suffix_ids)])
    rf = ArmConfig("ONE", gain=0.5, readout_mode="RF")
    state = engine.prefill(setup["prefixes"])
    log = engine.run_reflection(state, _plan(setup, rf, state.rows), ticks=4, write=True)
    assert bool((log["inj_ratio"][0::2] > 0).all()) and bool((log["inj_ratio"][1::2] == 0).all())
    before = _state_fingerprint(state)
    out = engine.run_readout(state, [(0, "A")], suffix, rf, [None], require_tick=4)
    assert "r_inj_ratio" not in out  # recipient alone, bridge off
    assert _same(before, _state_fingerprint(state))
    ro = ArmConfig("ONE", gain=0.5, readout_mode="RO")
    state = engine.prefill(setup["prefixes"])
    ema0 = state.ema.clone()
    log = engine.run_reflection(state, _plan(setup, ro, state.rows), ticks=4, write=False)
    assert bool((log["inj_ratio"] == 0).all())
    assert not torch.equal(state.ema, ema0)  # messages still update without writes
    out = engine.run_readout(state, [(0, "A")], suffix, ro, [None], require_tick=4)
    assert bool((out["r_inj_ratio"] > 0).all())


def test_record_mode_hook_observes_prefill_and_ticks(setup):
    """Calibration observers must not trip the one-token tick assertion during prefill."""
    from mb.bridge import BridgeHook

    engine, model = setup["engine"], setup["model"]
    hook = BridgeHook(model.model.layers[11], 12, record_all=True)
    hook.mode = "record"
    try:
        state = engine.prefill(setup["prefixes"])
        engine.run_reflection(state, _plan(setup, ArmConfig("C0"), state.rows), ticks=3)
        assert len(hook.records) == 1 + 3
        assert all(z.shape == (state.rows, engine.d) for _, z in hook.records)
    finally:
        hook.remove()


# --- protocol v2: KV reading ------------------------------------------------------------------


def _kv_plan(setup, rows, w=1.0, scope="ALL", two=False):
    import math

    from mb.runtime import KVPlan

    e = setup["engine"]
    receivers = torch.tensor([two or i % 2 == 0 for i in range(rows)], device=e.device)
    return KVPlan(receivers, math.log(w) if w > 0 else -math.inf, scope)


def test_kv_attention_inactive_is_plain_sdpa(setup):
    """The KV-capable attention must be bit-identical to sdpa whenever no KV plan is active."""
    engine, model = setup["engine"], setup["model"]
    runs = []
    for impl in ("sdpa", "mb_kv"):
        model.config._attn_implementation = impl
        state = engine.prefill(setup["prefixes"])
        logits, _, _ = engine.step(state, state.pending, None)
        runs.append((state.logits.clone(), logits))
    model.config._attn_implementation = "mb_kv"
    assert torch.equal(runs[0][0], runs[1][0]) and torch.equal(runs[0][1], runs[1][1])


def test_kv_reading_refuses_to_switch_off_silently(setup):
    """If the attention implementation is not the KV one, a KV tick must fail loudly."""
    engine, model = setup["engine"], setup["model"]
    state = engine.prefill(setup["prefixes"])
    model.config._attn_implementation = "sdpa"
    try:
        with pytest.raises(RuntimeError, match="KV reading ran in 0 layers"):
            engine.step(state, state.pending, None, kv=_kv_plan(setup, state.rows, w=1.0))
    finally:
        model.config._attn_implementation = "mb_kv"


def test_kv_zero_weight_equals_no_reading(setup):
    engine = setup["engine"]
    base = engine.prefill(setup["prefixes"])
    from mb.runtime import select_rows

    a = select_rows(base, list(range(base.rows)), setup["model"].config)
    b = select_rows(base, list(range(base.rows)), setup["model"].config)
    la, _, _ = engine.step(a, a.pending, None)
    lb, _, _ = engine.step(b, b.pending, None, kv=_kv_plan(setup, b.rows, w=0.0))
    assert torch.equal(la[1::2], lb[1::2]), "non-receivers must be untouched"
    # The mixture form makes w = 0 exact: the receiver keeps the plain attention output.
    assert torch.equal(la[0::2], lb[0::2]), "w=0 receivers deviate from plain attention"
    mass = engine.last_kv_mass
    assert bool((mass[0::2] == 0).all()) and bool(mass[1::2].isnan().all())


def test_kv_one_way_reads_partner_with_one_tick_delay(setup):
    """A reads B's cache; B's current-tick token is invisible to A until the next tick; B never reads A."""
    from mb.runtime import select_rows

    engine, cfg = setup["engine"], setup["model"].config
    base = engine.prefill(setup["prefixes"])
    kv = _kv_plan(setup, base.rows, w=1.0, scope="ALL")
    c, d = select_rows(base, list(range(base.rows)), cfg), select_rows(base, list(range(base.rows)), cfg)
    tok_c, tok_d = c.pending.clone(), d.pending.clone()
    tok_d[1::2] = (tok_d[1::2] + 7) % 1000 + 100  # change only B's current token
    lc, _, _ = engine.step(c, tok_c, None, kv=kv)
    ld, _, _ = engine.step(d, tok_d, None, kv=kv)
    assert torch.equal(lc[0::2], ld[0::2]), "A saw B's same-tick token"
    lc2, _, _ = engine.step(c, lc.argmax(-1), None, kv=kv)
    ld2, _, _ = engine.step(d, lc.argmax(-1), None, kv=kv)
    assert not torch.allclose(lc2[0::2], ld2[0::2]), "B's token never reached A"
    # B's own computation does not depend on A: perturb A only.
    e, f = select_rows(base, list(range(base.rows)), cfg), select_rows(base, list(range(base.rows)), cfg)
    tok_f = f.pending.clone()
    tok_f[0::2] = (tok_f[0::2] + 7) % 1000 + 100
    le, _, _ = engine.step(e, e.pending, None, kv=kv)
    lf, _, _ = engine.step(f, tok_f, None, kv=kv)
    le2, _, _ = engine.step(e, le.argmax(-1), None, kv=kv)
    lf2, _, _ = engine.step(f, le.argmax(-1), None, kv=kv)
    assert torch.equal(le2[1::2], lf2[1::2]), "B read A in a one-way arm"
    mass = engine.last_kv_mass
    assert bool(((mass[0::2] > 0) & (mass[0::2] < 1)).all())


def test_kv_scope_and_arm_wiring(setup):
    """Scope C reads only C-phase partner tokens; KV arms run end to end through reflection and readout."""
    from mb.runtime import make_plan

    engine, tok = setup["engine"], setup["tok"]
    arm = ArmConfig("TWO", gain=1.0, interface="kv", kv_scope="C", recipients=("A", "B"))
    plan = make_plan(arm, ["A", "B"] * (len(setup["prefixes"]) // 2), [None] * len(setup["prefixes"]),
                     None, engine.device, d=engine.d)
    assert plan.kv is not None and bool(plan.kv.receivers.all()) and not plan.writes
    state = engine.prefill(setup["prefixes"])
    log = engine.run_reflection(state, plan, ticks=4)
    # First tick: scope C has no committed partner C token yet, so nothing can be read.
    assert float(log["kv_mass"][:, 0].nan_to_num(0).max()) == 0.0
    assert bool((log["kv_mass"][:, -1] > 0).all())
    q = tasks.make_question(tok, setup["eps"][0], "A", "START", 0)
    out = engine.run_readout(state, [(0, "A"), (0, "B")], torch.tensor([list(q.suffix_ids)] * 2), arm, [None, None],
                             require_tick=4)
    assert out["label_logits"].shape == (2, 4) and bool((out["r_kv_mass_mean"] > 0).all())


def test_kv_pc_split_weights_reduce_to_single_scopes(setup):
    """Protocol v3 KV-PC: w_C = 0 equals scope P with the same w_P; w_P = 0 equals scope C with w = w_C."""
    import math

    from mb.runtime import KVPlan, select_rows

    engine, cfg = setup["engine"], setup["model"].config
    state = engine.prefill(setup["prefixes"])
    engine.run_reflection(state, _plan(setup, ArmConfig("C0"), state.rows), ticks=3)
    recv = torch.tensor([i % 2 == 0 for i in range(state.rows)], device=engine.device)
    pairs = [(KVPlan(recv, math.log(2.0), "PC", -math.inf), KVPlan(recv, math.log(2.0), "P")),
             (KVPlan(recv, -math.inf, "PC", 0.0), KVPlan(recv, 0.0, "C"))]
    for pc, single in pairs:
        s1 = select_rows(state, list(range(state.rows)), cfg)
        s2 = select_rows(state, list(range(state.rows)), cfg)
        l1, _, _ = engine.step(s1, s1.pending, None, kv=pc)
        l2, _, _ = engine.step(s2, s2.pending, None, kv=single)
        assert float((l1 - l2).abs().max()) < 1e-2 and torch.equal(l1.argmax(-1), l2.argmax(-1))
