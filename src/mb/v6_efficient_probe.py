"""Inert preparation and guarded operator feasibility, never a model benchmark.

No CLI dispatches CUDA. A future separately reviewed controller must supply
hardware authorization and its live deadline/lease check to run_operator_probe.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import statistics
import sys
import time
import traceback
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import numpy as np

from mb.v6_efficient import (KERNELS, VERSION, JointKernel, Layout,
                             bias_policy, diagnostic_error, scalar_oracle)
from mb.v6_flex_compile import compile_policy

ENGINEERING_LIMIT = 2 ** -7


def layouts() -> tuple[Layout, ...]:
    # A bounded covering set, not a large Cartesian CUDA compilation sweep.
    cases = [Layout(1, 4, 2, 1, 7, window, 16, gain)
             for window in (0, 1, 16) for gain in (0., .25, .5, 1.)]
    cases += [Layout(batch, 4, 2, queries, prefix, 16, 16, .5)
              for batch, queries, prefix in ((2, 2, 0), (4, 4, 7), (8, 1, 7), (8, 4, 31))]
    return tuple(cases)


def source_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    names = ("src/mb/v6_efficient.py", "src/mb/v6_efficient_native.py",
             "src/mb/v6_flex_compile.py",
             "src/mb/v6_efficient_probe.py", "src/mb/v6_native.py",
             "src/mb/v6_contract.py", "src/mb/model_profiles.py",
             "docs/protocol/V6_NUMERICAL_ACCEPTANCE_DRAFT.md",
             "docs/runbooks/V6_SDPA_DTYPE_REPAIR_20261016.md",
             "docs/runbooks/V6_FLEX_COMPILE_REPAIR_20261016.md")
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}


def write_new(path: Path, value: dict) -> None:
    with path.open("x") as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def prepare(directory: Path, kernel: str) -> dict:
    if kernel not in KERNELS:
        raise ValueError("Name exactly one fused candidate")
    package = {"version": VERSION, "kernel": kernel, "source_sha256": source_hashes(),
        "operator_bias_policy": bias_policy(),
        "flex_compile_policy": compile_policy(),
        "operator_cases": [asdict(case) for case in layouts()], "seed": 940215,
        "timing_repeats": 5, "engineering_max_abs_over_value_scale": ENGINEERING_LIMIT,
        "scientific_admission": False, "paid_launch_authorized": False,
        "formal_authorized": False, "model_loading": False,
        "scope": "synthetic_operator_correctness_and_timing_only",
        "runtime_contract": {"torch": "2.6.0", "transformers": "4.57.1", "matmul_tf32": False},
        "automatic_continuation": False, "whole_experiment_forecast_allowed": False}
    directory.mkdir(parents=True, exist_ok=False)
    write_new(directory / "package.json", package)
    return package


def validate_package(package: dict) -> None:
    if (package.get("version") != VERSION or package.get("kernel") not in KERNELS
            or package.get("operator_bias_policy") != bias_policy()
            or package.get("flex_compile_policy") != compile_policy()
            or package.get("source_sha256") != source_hashes()
            or package.get("operator_cases") != [asdict(case) for case in layouts()]
            or package.get("seed") != 940215 or package.get("timing_repeats") != 5
            or package.get("engineering_max_abs_over_value_scale") != ENGINEERING_LIMIT
            or package.get("runtime_contract") != {"torch": "2.6.0", "transformers": "4.57.1", "matmul_tf32": False}
            or any(package.get(key) is not False for key in (
                "scientific_admission", "paid_launch_authorized", "formal_authorized",
                "model_loading", "automatic_continuation", "whole_experiment_forecast_allowed"))
            or package.get("scope") != "synthetic_operator_correctness_and_timing_only"):
        raise ValueError("Changed or unbound engineering package")


def error_screen(reference: np.ndarray, actual: np.ndarray, values: tuple[np.ndarray, ...]) -> dict:
    scale = max(float(np.max(np.abs(x))) if x.size else 0. for x in values)
    report = diagnostic_error(reference, actual, scale)
    report["engineering_screen_pass"] = bool(report["max_abs"] <= ENGINEERING_LIMIT * scale)
    report["engineering_limit"] = ENGINEERING_LIMIT
    return report


def old_operator(layout: Layout, arrays: tuple[Any, ...]) -> Any:
    """Call the unchanged native single-history, single-token mixing operation.

    This excludes model projections, logits and archives. Its timing is never a
    substitute for a full-model or full-episode benchmark.
    """
    import torch
    from mb.v6_native import _AttentionContext, _FORWARD, _attention
    q, k, v, fk, fv = arrays
    module = SimpleNamespace(num_key_value_groups=layout.heads // layout.kv_heads, training=False)
    rows = []
    for lane in range(layout.batch):
        tokens = []
        for token in range(layout.queries):
            layers = ((fk[lane:lane+1], fv[lane:lane+1]),) if layout.foreign else ()
            context = _AttentionContext({id(module): 0}, layers, layout.gain)
            handle = _FORWARD.set(context)
            try:
                result, _ = _attention(module, q[lane:lane+1, :, token:token+1],
                    k[lane:lane+1, :, :layout.prefix+token+1],
                    v[lane:lane+1, :, :layout.prefix+token+1], None, is_causal=False)
                tokens.append(result.transpose(1, 2))
            finally:
                _FORWARD.reset(handle)
        rows.append(torch.cat(tokens, dim=2))
    return torch.cat(rows, dim=0)


def paired_timing(functions: dict[str, Callable[[], Any]], check: Callable[[], None],
                  emit: Callable[[dict], None], order_offset: int) -> dict:
    import torch
    elapsed = {name: [] for name in functions}
    for repeat in range(5):
        names = tuple(functions)
        if (repeat + order_offset) % 2:
            names = names[::-1]
        for name in names:
            check()
            torch.cuda.synchronize()
            start = time.monotonic()
            result = functions[name]()
            torch.cuda.synchronize()
            seconds = time.monotonic() - start
            finite = bool(torch.isfinite(result).all())
            elapsed[name].append(seconds)
            emit({"phase": "timing_sample", "implementation": name, "repeat": repeat,
                  "order": list(names), "seconds": seconds, "finite": finite})
            check()
            if not finite:
                raise ValueError("Nonfinite timed output")
    return {name: {"seconds": samples, "median_seconds": statistics.median(samples)}
            for name, samples in elapsed.items()}


def save_arrays(path: Path, values: dict[str, Any]) -> None:
    with path.open("xb") as handle:
        np.savez_compressed(handle, **values)
        handle.flush()
        os.fsync(handle.fileno())


def runtime_environment(kernel: str) -> dict:
    import torch
    transformers = importlib.metadata.version("transformers")
    if (torch.__version__.split("+")[0] != "2.6.0" or transformers != "4.57.1"
            or not torch.cuda.is_available() or torch.backends.cuda.matmul.allow_tf32):
        raise RuntimeError("Require pinned torch2.6.0/transformers4.57.1 CUDA, with matmul TF32 disabled")
    return {"torch": torch.__version__, "transformers": transformers, "numpy": np.__version__,
        "python": sys.version, "cuda": torch.version.cuda, "device": torch.cuda.get_device_name(),
        "kernel": kernel, "math_fallback_allowed": False,
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark, "cudnn_tf32": torch.backends.cudnn.allow_tf32,
        "matmul_tf32": torch.backends.cuda.matmul.allow_tf32,
        "bf16_reduced_precision_reduction": torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction,
        "flash_sdp_enabled": torch.backends.cuda.flash_sdp_enabled(),
        "mem_efficient_sdp_enabled": torch.backends.cuda.mem_efficient_sdp_enabled(),
        "math_sdp_enabled_for_reference": torch.backends.cuda.math_sdp_enabled()}


def inspect_case(layout: Layout, tensors: tuple[Any, ...], kernel: JointKernel,
                 check: Callable[[], None], evidence: Path,
                 emit: Callable[[dict], None], order_offset: int) -> dict:
    import torch
    cpu = tuple(x.float().cpu().numpy().astype(np.float64) for x in tensors)
    expected = scalar_oracle(layout, cpu)
    save_arrays(evidence / "inputs.npz", dict(zip(("q", "k", "v", "fk", "fv"), cpu)) | {"oracle": expected})
    emit({"phase": "oracle_complete", "layout": asdict(layout)})
    check()
    torch.cuda.synchronize()
    start = time.monotonic()
    actual = kernel(layout, tensors)
    torch.cuda.synchronize()
    first_seconds = time.monotonic() - start
    observed = actual.float().cpu().numpy().astype(np.float64)
    save_arrays(evidence / "candidate.npz", {"output": observed})
    report = error_screen(expected, observed, (cpu[2], cpu[4]))
    report.update({"layout": asdict(layout), "first_call_compile_warmup_seconds": first_seconds,
                   "compilation": kernel.compilation_report(),
                   "strict_checks": {}, "scientific_admission": False})
    emit({"phase": "candidate_numeric", "report": report})
    check()
    if not report["engineering_screen_pass"]:
        report["status"] = "failed"
        return report

    def compare(name: str, wanted: Any, found: Any) -> None:
        passed = bool(torch.equal(wanted, found))
        report["strict_checks"][name] = passed
        save_arrays(evidence / f"{name}.npz", {"expected": wanted.float().cpu().numpy(),
                   "observed": found.float().cpu().numpy()})
        emit({"phase": "strict_check", "name": name, "passed": passed})
        check()
        if not passed:
            raise ValueError(f"Strict invariant failed: {name}")

    compare("repeat", actual, kernel(layout, tensors))
    if layout.batch > 1:
        changed = tuple(x.clone() for x in tensors)
        for tensor in changed:
            tensor[-1] += 3
        check()
        compare("lane_isolation", actual[:-1], kernel(layout, changed)[:-1])
        order = torch.arange(layout.batch-1, -1, -1, device=tensors[0].device)
        compare("lane_permutation", actual[order], kernel(layout, tuple(x[order] for x in tensors)))
        singleton = kernel(replace(layout, batch=1), tuple(x[:1] for x in tensors))
        save_arrays(evidence / "singleton.npz", {"output": singleton.float().cpu().numpy()})
        report["singleton_error"] = error_screen(expected[:1], singleton.float().cpu().numpy(), (cpu[2][:1], cpu[4][:1]))
        emit({"phase": "singleton_numeric", "report": report["singleton_error"]})
        check()
        if not report["singleton_error"]["engineering_screen_pass"]:
            report["status"] = "failed"
            return report
    if layout.queries > 1:
        changed = tuple(x.clone() for x in tensors)
        changed[1][:, :, layout.prefix+1:] += 5
        changed[2][:, :, layout.prefix+1:] -= 5
        check()
        compare("own_future_isolation", actual[:, :, 0], kernel(layout, changed)[:, :, 0])
    report["strict_checks"]["input_nonmutation"] = all(
        np.array_equal(old, now.float().cpu().numpy()) for old, now in zip(cpu, tensors))
    emit({"phase": "numerical_and_invariants_complete", "report": report})
    check()
    if (not report["engineering_screen_pass"] or not all(report["strict_checks"].values())
            or not report.get("singleton_error", {"engineering_screen_pass": True})["engineering_screen_pass"]):
        report["status"] = "failed"
        return report
    # Synchronize/warm the reference outside its primary repeated timer.
    reference = old_operator(layout, tensors)
    torch.cuda.synchronize()
    save_arrays(evidence / "old_operator.npz", {"output": reference.float().cpu().numpy()})
    report["old_operator_error"] = error_screen(expected, reference.float().cpu().numpy(), (cpu[2], cpu[4]))
    emit({"phase": "old_operator_numeric", "report": report["old_operator_error"]})
    check()
    if not report["old_operator_error"]["engineering_screen_pass"]:
        report["status"] = "failed"
        return report
    report.update(paired_timing({"candidate": lambda: kernel(layout, tensors),
        "old_serial_operator": lambda: old_operator(layout, tensors)}, check, emit, order_offset))
    report["operator_only_speedup"] = report["old_serial_operator"]["median_seconds"] / report["candidate"]["median_seconds"]
    report["status"] = "engineering_screen_pass"
    return report


def run_operator_probe(package: dict, directory: Path, *, check: Callable[[], None],
                       hardware_authorized: bool = False) -> dict:
    """No retries, provider access, model loading or automatic scientific step."""
    if hardware_authorized is not True or not callable(check):
        raise PermissionError("Separate protected hardware authorization and live check required")
    validate_package(package)
    check()
    directory.mkdir(parents=True, exist_ok=False)
    write_new(directory / "package.json", package)
    kernel = None
    try:
        import torch
        write_new(directory / "environment.json", runtime_environment(package["kernel"]))
        kernel = JointKernel(package["kernel"])
        rng = np.random.default_rng(package["seed"])
        for index, layout in enumerate(layouts()):
            check()
            # Oracle sees the actual BF16 inputs after their round-trip, not the
            # higher-precision random values used to construct them.
            values = tuple(torch.tensor(rng.normal(size=shape), device="cuda", dtype=torch.bfloat16)
                           for shape in layout.shapes)
            write_new(directory / f"case-{index:03d}-intent.json", {"layout": asdict(layout), "seed": package["seed"]})
            evidence = directory / f"case-{index:03d}-evidence"
            evidence.mkdir()
            with (evidence / "progress.jsonl").open("x") as progress:
                def emit(event: dict) -> None:
                    progress.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                    progress.flush()
                    os.fsync(progress.fileno())
                with torch.no_grad():
                    result = inspect_case(layout, values, kernel, check, evidence, emit, index)
            write_new(directory / f"case-{index:03d}.json", result)
            check()
            if result["status"] != "engineering_screen_pass":
                raise ValueError("Predetermined operator screen failed; no tolerance change/retry")
        check()
        summary = {"version": VERSION, "operator_cases_complete": len(layouts()),
            "compilation": kernel.compilation_report(),
            "status": "operator_screen_complete_model_integration_unverified",
            "scientific_admission": False, "whole_experiment_forecast_allowed": False,
            "automatic_continuation": False}
        write_new(directory / "summary.json", summary)
        return summary
    except BaseException as exc:
        write_new(directory / "failure.json", {"error_type": type(exc).__name__,
            "compilation": kernel.compilation_report() if kernel is not None else None,
            "error": str(exc), "scientific_admission": False, "automatic_continuation": False})
        (directory / "failure_traceback.txt").write_text(traceback.format_exc())
        raise
