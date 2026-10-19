"""Finite partner-goal intervention with separate work and readout channels."""
from __future__ import annotations

from dataclasses import asdict, replace

from mb import v6_channel_diagnostic as channel, v6_tasks as tasks

CONTRACT = "v6-partner-goal-stage-exploration-20261019-v1"
QIDS = ("own_rule", "latest_goal", "partner_goal", "partner_beacon", "action")


def materials() -> tuple[tasks.Episode, ...]:
    # Reuse both complete initial layouts, not a subset selected by their errors.
    return tuple(replace(ep, episode_id=ep.episode_id.replace("channel_explore", "goal_stage"),
                         stage="v6_goal_stage_20261019") for ep in channel.materials())


def donor_variant(ep: tasks.Episode, focal: int, goal: int):
    if focal not in (0, 1) or goal not in range(4) or goal == ep.original_goals[focal]:
        raise ValueError("Expected a distinct partner assignment and a physical focal side")
    goals = list(ep.original_goals)
    goals[1-focal] = goal
    system, users = channel.clarity.initial_prompts(ep, "P2")
    users = list(users)
    old = f"Your original assigned goal: {ep.goal_names[ep.original_goals[1-focal]]}."
    new = f"Your original assigned goal: {ep.goal_names[goal]}."
    if users[1-focal].count(old) != 1:
        raise RuntimeError("Initial assignment template changed")
    users[1-focal] = users[1-focal].replace(old, new)
    return replace(tasks.initial_world(ep), goals=tuple(goals)), system, tuple(users)


def question(ep, world, side, qid):
    if qid not in QIDS:
        raise ValueError("Unknown stage diagnostic readout")
    if qid == "partner_goal":
        return tasks.question(ep, world, side, qid)
    return channel.question(ep, world, side, qid)


class GoalStageRunner(channel.pilot.PilotRunner):
    """All answers are discarded; the world never advances after initialization."""

    def _read(self, ep, pair, side, qid, held, checkpoint):
        q = question(ep, pair.world, side, qid)
        before = self.digest(pair)
        p = self.backend.probe(pair.models[side], q.text, self.spec.choice_labels,
                               held[side], self.spec.gain)
        p.validate()
        if self.digest(pair) != before:
            raise RuntimeError("Stage readout mutated the common post-work pair")
        choice = q.candidates[p.token_ids.index(p.token)] if p.token in p.token_ids else None
        detail = {"question": q.text, "world": asdict(pair.world)}
        if self.probe_sink:
            detail.update(self.probe_sink(p))
        self._pending[id(p)] = detail
        return q, p, choice

    def run_diagnostic(self, ep: tasks.Episode, *, reverse_order: bool = False):
        self.records, self.audit, self._pending, self.stage_audit = [], [], {}, []
        self._episode_id, self._artifact_sequence = ep.episode_id, 0
        initial = self.initialize(ep)
        original = self.digest(initial)
        self.archive("pair", initial, "common_initial_pair")
        system, users = channel.clarity.initial_prompts(ep, "P2")
        own_initial = [self.backend.digest(s) for s in initial.models]
        own_prepared, off_states = {}, {}
        order = lambda seq: tuple(reversed(seq)) if reverse_order else tuple(seq)
        for focal in order((0, 1)):
            for donor_goal in order(tuple(g for g in range(4) if g != ep.original_goals[focal])):
                world, new_system, new_users = donor_variant(ep, focal, donor_goal)
                if new_system != system or new_users[focal] != users[focal]:
                    raise RuntimeError("Partner intervention changed the recipient prompt")
                base = self.clone(initial)
                if donor_goal != ep.original_goals[1-focal]:
                    donor = self.backend.create(system, new_users[1-focal])
                    for _ in range(self.spec.preparation_tokens):
                        self.backend.step(donor, (), 0.0)
                    self.backend.finish_turn(donor)
                    models = list(base.models)
                    models[1-focal] = donor
                    base.models = tuple(models)
                base.world = replace(world, round_id=1)
                if self.backend.digest(base.models[focal]) != own_initial[focal]:
                    raise RuntimeError("Partner intervention changed initial recipient state")
                messages = channel.pilot.round_messages(ep, base.world, (False, False))
                for side in (0, 1):
                    self.backend.begin_user(base.models[side], messages[side])
                prepared = self.backend.digest(base.models[focal])
                own_prepared.setdefault(focal, prepared)
                if own_prepared[focal] != prepared:
                    raise RuntimeError("Recipient preparation differs across partner goals")
                base_digest = self.digest(base)
                for work_on in order((False, True)):
                    pair = self.clone(base)
                    self.context = {"focal_side": focal, "donor_goal": donor_goal,
                                    "work_on": work_on}
                    audit_start = len(self.audit)
                    self.work(pair, "LIVE" if work_on else "OFF")
                    state_digest = self.backend.digest(pair.models[focal])
                    if not work_on:
                        off_states.setdefault(focal, state_digest)
                        if off_states[focal] != state_digest:
                            raise RuntimeError("Disconnected work depends on partner assignment")
                    parent = self.digest(pair)
                    exports = pair.windows[1-focal]
                    for read_on in order((False, True)):
                        held = tuple(pair.windows[1-s] if read_on else () for s in (0, 1))
                        meta = {"kind": "goal_stage", "policy": "LIVE" if work_on else "OFF",
                                "checkpoint": 1, "arm": f"W{int(work_on)}R{int(read_on)}",
                                "version": donor_goal+1, "focal_side": focal,
                                "donor_goal": donor_goal, "work_on": work_on,
                                "read_on": read_on, "recipient_prepared_digest": prepared,
                                "recipient_postwork_digest": state_digest,
                                "postwork_pair_digest": parent,
                                "readout_incoming": [x.identity() for x in held[focal]],
                                "available_partner_exports": [x.identity() for x in exports]}
                        for qid in QIDS:
                            q, p, choice = self._read(ep, pair, focal, qid, held, 0)
                            self.emit(ep, pair, focal, q, p, choice, meta)
                    if self.digest(pair) != parent or self.digest(base) != base_digest:
                        raise RuntimeError("A diagnostic branch changed a parent")
                    self.stage_audit.append({**self.context, "prepared_pair_digest": base_digest,
                        "recipient_prepared_digest": prepared, "recipient_postwork_digest": state_digest,
                        "postwork_pair_digest": parent, "world": asdict(pair.world),
                        "audit_start": audit_start, "audit_end": len(self.audit)})
                if self.digest(initial) != original:
                    raise RuntimeError("Partner variant contaminated the original pair")
        if len(self.records) != 120 or self._pending or len(self.stage_audit) != 12:
            raise RuntimeError("Incomplete finite goal-stage comparison")
        return self.records


def plan() -> dict:
    return {"contract": CONTRACT, "episodes": [asdict(ep) for ep in materials()],
        "exposed_initial_layouts": True, "focal_sides": [0, 1],
        "partner_goals": "all three assignments distinct from fixed recipient goal",
        "arms": ["W0R0", "W0R1", "W1R0", "W1R1"], "qids": list(QIDS),
        "records": 240, "gain": 1.0, "work_tokens": 64, "preparation_tokens": 16,
        "window": 16, "self_report": False, "world_action_commits": 0,
        "backend": "original_native", "formal_authorized": False,
        "scientific_admission": False, "automatic_continuation": False,
        "outcome_threshold": None, "second_episode_execution_order": "reversed"}
