#!/usr/bin/env python3
"""Run the M2 closed-loop public demo offline: needs -> contract -> review -> rating.

This script reproduces only the offline, runnable part of the M2
power-distribution closed loop, using cleaned/synthetic public data:

    1. requirements gate   -> hardware-contract.json      (scripts/requirements-gate.py)
    2. prototype review    -> machine-review.json and the Chinese report/summary
                             files                         (src/review/prototype_review.py)
    3. demo summary        -> demo-summary.zh.md           (this script)

Honesty contract:

- The full governed loop (real EDA schematic/PCB drawing, allow-listed
  ADD_LOCAL_BYPASS_CAP correction, save/close/reload and independent readback,
  then a fresh review) was completed and passed in the real EDA environment.
  This script does NOT replay that part: it performs no EDA access, no drawing
  and no automatic correction. It only shows needs -> spec -> review -> rating.
- ``--now`` pins every timestamp so two runs are byte-identical (same
  convention as ``scripts/requirements-gate.py --now``). When omitted, real
  run-time timestamps are used.

Usage:
    python scripts/run-closed-loop-demo.py [--requirements ...] [--design ...]
        [--out ...] [--profiles ...] [--now <ISO8601>]

Exit code 0 when the whole chain succeeds; non-zero with an error on stderr
otherwise.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

DEFAULT_REQUIREMENTS = REPO / "examples" / "m2-closed-loop" / "requirements.zh.json"
DEFAULT_DESIGN = REPO / "examples" / "m2-closed-loop" / "design-data.json"
DEFAULT_OUT = REPO / "examples" / "m2-closed-loop" / "output"
DEFAULT_PROFILES = REPO / "src" / "review" / "component-profiles.json"

GATE_SCRIPT = REPO / "scripts" / "requirements-gate.py"
REVIEW_SCRIPT = REPO / "src" / "review" / "prototype_review.py"

CONTRACT_NAME = "hardware-contract.json"
REVIEW_NAME = "machine-review.json"
REPORT_NAME = "prototype-review-report-zh.md"
SUMMARY_NAME = "demo-summary.zh.md"

# Every artifact this demo owns; removed before a run so the output directory
# reflects exactly the current invocation (deterministic, no stale leftovers).
OWNED_ARTIFACTS = (
    CONTRACT_NAME,
    REVIEW_NAME,
    REPORT_NAME,
    "one-page-summary-zh.md",
    "firmware-pin-map.csv",
    "screenshot-index.json",
    "evidence-manifest.json",
    SUMMARY_NAME,
)


def _run_python(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a repository Python entry point with -B and UTF-8 capture."""
    return subprocess.run(
        [sys.executable, "-B", *[str(arg) for arg in args]],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _fail(message: str, *, output: str = "") -> int:
    print(f"closed-loop demo FAILED: {message}", file=sys.stderr)
    if output:
        print(output, file=sys.stderr)
    return 2


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _pin_generated_at(path: Path, value: str) -> None:
    """Pin generatedAt so reruns with the same --now are byte-identical."""
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("generatedAt") != value:
        document["generatedAt"] = value
        _write_json(path, document)


def _refresh_manifest_hashes(manifest_path: Path) -> None:
    """Recompute evidence-manifest file digests after timestamp pinning.

    The engine computes the manifest digests before this script pins
    generatedAt in machine-review.json, so those two entries would otherwise
    stay stale and make reruns differ. Recompute them from the pinned files.
    """
    import hashlib

    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in document.get("files", []):
        target = manifest_path.parent / entry["path"]
        entry["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest().upper()
        entry["bytes"] = target.stat().st_size
    _write_json(manifest_path, document)


def _pin_timestamps(out: Path, now: str) -> None:
    """Pin the two engine timestamps (the gate pins its own via --now)."""
    _pin_generated_at(out / REVIEW_NAME, now)
    manifest_path = out / "evidence-manifest.json"
    _pin_generated_at(manifest_path, now)
    _refresh_manifest_hashes(manifest_path)


def _render_components(contract: dict) -> str:
    def label(component: dict) -> str:
        name = component["name"] or ""
        designator = component["designator"]
        if designator and designator not in name:
            return f"{designator}({name})"
        return name or designator or "未命名"

    entries = [label(c) for c in contract["components"]]
    return f"{len(entries)} 个 —— " + "、".join(entries)


def _render_domains(contract: dict) -> str:
    def fmt(domain: dict) -> str:
        nominal = domain.get("nominalVoltageV")
        minimum = domain.get("minVoltageV")
        maximum = domain.get("maxVoltageV")
        current = domain.get("maxCurrentA")
        return (
            f"{domain['name']}(标称 {nominal:g}V,范围 {minimum:g}–{maximum:g}V,"
            f"{current:g}A)"
        )
    return "、".join(fmt(d) for d in contract["powerDomains"])


def _blocker_details(result: dict) -> str:
    blockers = [f for f in result["findings"] if f["severity"] == "blocker"]
    if not blockers:
        return "无"
    lines = []
    for f in blockers:
        lines.append(f"- `{f['id']}` —— {f['title']}")
        if f.get("evidence"):
            lines.append(f"  - 证据:{json.dumps(f['evidence'], ensure_ascii=False)}")
        if f.get("locations"):
            lines.append(f"  - 位置:{', '.join(f['locations'])}")
    return "\n".join(lines)


def _group_findings(result: dict, severity: str) -> list[str]:
    return [f["id"] for f in result["findings"] if f["severity"] == severity]


def _render_summary(contract: dict, result: dict, *, out: Path, now: str | None) -> str:
    counts = result["counts"]
    unresolved = contract["unresolved"]
    unresolved_text = "\n".join(f"  - {u}" for u in unresolved) or "  - 无"
    generated_at = contract["generatedAt"]
    timestamp_note = (
        f"所有时间戳已由 `--now {now}` 固定,两次运行输出字节一致。"
        if now
        else "未指定 `--now`,时间戳为本次运行实际时间。"
    )
    lines = [
        "# M2 电源分配板 — 端到端闭环公开示例(离线部分)",
        "",
        "> **NOT FOR MANUFACTURING(不可直接制造)**",
        ">",
        "> 本示例用清洗/合成数据复现「中文需求 → 硬件规格(hardware-contract)→ 自动审核 → 评级」",
        "> 这条**可离线运行**的链路。完整闭环(含真实 EDA 画板、白名单修正、保存重载复验)",
        "> 已在真实嘉立创 EDA 环境中完成并通过;本示例不在此处自动画板、不执行任何 EDA 写入",
        "> 或自动修正。",
        "",
        "## 一、输入",
        "",
        f"- 需求:`{DEFAULT_REQUIREMENTS.relative_to(REPO).as_posix()}`(清洗后的中文需求)",
        f"- 设计数据:`{DEFAULT_DESIGN.relative_to(REPO).as_posix()}`(合成坐标/网络的审核输入,BEFORE 状态)",
        "",
        "## 二、需求 → 硬件规格(hardware-contract.json)",
        "",
        f"- 状态:`{contract['status']}`(fail-closed:缺失事实记录为未决项,不猜测)",
        f"- 生成时间:`{generated_at}`",
        f"- 组件(components):{_render_components(contract)}",
        f"- 电源域(powerDomains):{_render_domains(contract)}",
        f"- 信号(signals):{len(contract['signals'])} 个",
        f"- 未决项(unresolved):{len(unresolved)} 条",
        unresolved_text,
        "",
        f"- {timestamp_note}",
        "",
        "## 三、自动审核(machine-review.json / prototype-review-report-zh.md)",
        "",
        f"- 评级:`{result['rating']}`(当前不适合样板)",
        f"- blocker:{counts['blocker']} 个(唯一)",
        _blocker_details(result),
        f"- advisory:{counts['advisory']} 个 —— " + "、".join(_group_findings(result, "advisory")),
        f"- pass:{counts['pass']} 个 —— " + "、".join(_group_findings(result, "pass")),
        "",
        "## 四、真实闭环在哪里完成过",
        "",
        "真实 M2 案例中,上述唯一 blocker 经白名单修正(在 J2 附近新增一颗 100nF 旁路电容)",
        "→ 在真实 EDA 中改图 → 保存重载 → 独立读回 → 复审,评级提升为",
        "`suitable_for_low_risk_prototype`。该闭环**已真实发生并通过**;",
        "本公开示例只复现上面第二、三节这段可离线运行的链路,坐标与网络均为合成值,",
        "不含任何私有 EDA 信息(UUID/器件ID/审批记录/截图路径)。",
        "",
        "## 五、如何复现",
        "",
        "```powershell",
        "python -B scripts/run-closed-loop-demo.py",
        "```",
        "",
        f"输出目录:`{out.as_posix()}/`。加 `--now <ISO8601>` 可固定全部时间戳。",
        "",
        "## 声明",
        "",
        "NOT FOR MANUFACTURING。本示例不构成打样放行、实物功能证明或 Manufacturing Release;",
        "离线重放结果不代表当前真实 EDA 文档状态。",
        "",
    ]
    return "\n".join(lines)


def _clean_output(out: Path) -> None:
    for name in OWNED_ARTIFACTS:
        target = out / name
        try:
            if target.is_file():
                target.unlink()
        except OSError:
            pass


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="M2 closed-loop public demo: needs -> contract -> review -> rating (offline)."
    )
    parser.add_argument("--requirements", type=Path, default=DEFAULT_REQUIREMENTS,
                        help="cleaned requirements-input JSON (default: examples/m2-closed-loop/requirements.zh.json)")
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN,
                        help="cleaned review input JSON (default: examples/m2-closed-loop/design-data.json)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="output directory (default: examples/m2-closed-loop/output)")
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES,
                        help="component profiles JSON (default: src/review/component-profiles.json)")
    parser.add_argument("--now", help="ISO 8601 timestamp; pins all generatedAt fields for byte-identical reruns")
    args = parser.parse_args(argv)

    requirements = args.requirements.resolve()
    design = args.design.resolve()
    profiles = args.profiles.resolve()
    out = args.out.resolve()

    for label, path in (("--requirements", requirements), ("--design", design), ("--profiles", profiles)):
        if not path.is_file():
            return _fail(f"{label} file not found: {path}")
    _clean_output(out)
    out.mkdir(parents=True, exist_ok=True)

    # ---- step 1: requirements gate ----
    gate_args = [GATE_SCRIPT, "--input", requirements, "--output", out / CONTRACT_NAME]
    if args.now:
        gate_args += ["--now", args.now]
    gate = _run_python(gate_args)
    if gate.returncode != 0:
        return _fail("requirements gate rejected the input", output=gate.stderr or gate.stdout)
    try:
        contract = _read_json(out / CONTRACT_NAME)
    except (OSError, json.JSONDecodeError) as exc:
        return _fail(f"could not read generated contract: {exc}")
    print(
        f"[1/3] requirements gate ......... {contract['status']} "
        f"({len(contract['components'])} components, {len(contract['unresolved'])} unresolved)"
    )

    # ---- step 2: prototype review ----
    review = _run_python([
        REVIEW_SCRIPT, "--input", design, "--profiles", profiles, "--output", out,
    ])
    if review.returncode != 0:
        return _fail("prototype review failed", output=review.stderr or review.stdout)
    try:
        result = _read_json(out / REVIEW_NAME)
    except (OSError, json.JSONDecodeError) as exc:
        return _fail(f"could not read review result: {exc}")
    counts = result["counts"]
    print(
        f"[2/3] prototype review .......... {result['rating']} "
        f"({counts['blocker']} blocker, {counts['advisory']} advisory, {counts['pass']} pass)"
    )

    # ---- step 3: deterministic timestamps + demo summary ----
    if args.now:
        _pin_timestamps(out, args.now)
    summary_path = out / SUMMARY_NAME
    summary_path.write_text(
        _render_summary(contract, result, out=out, now=args.now), encoding="utf-8"
    )
    print(f"[3/3] demo summary .............. {summary_path}")
    print("closed-loop demo OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
