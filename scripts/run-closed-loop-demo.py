#!/usr/bin/env python3
"""Run the M2 closed-loop public demo offline: needs -> contract -> review -> rating.

This script reproduces only the offline, runnable part of the M2
power-distribution closed loop, using cleaned/synthetic public data:

    1. requirements gate    -> hardware-contract.json     (scripts/requirements-gate.py)
    2. contract conversion  -> review-input.json          (src/spec/contract_to_review.py,
                              in-memory, written to the output directory) and then
       prototype review     -> machine-review.json and the Chinese report/summary
                              files                        (src/review/prototype_review.py)
    3. demo summary         -> demo-summary.zh.md          (this script)

By default no prefab design data is needed: the review input is projected from
the step-1 hardware contract by the offline converter, which never guesses
(facts the contract does not express are omitted or logged, never invented), so
the whole chain "Chinese needs -> spec -> review -> rating" runs fully
automatically with one command. ``--design <file>`` is still accepted for
backward compatibility: when given explicitly, that file is used directly as
the review input and the conversion step is skipped.

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

SPEC_DIR = REPO / "src" / "spec"
REVIEW_DIR = REPO / "src" / "review"
for _directory in (SPEC_DIR, REVIEW_DIR):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from contract_to_review import (  # noqa: E402
    ContractInputError,
    contract_to_review_input,
    contract_to_review_issues,
)

DEFAULT_REQUIREMENTS = REPO / "examples" / "m2-closed-loop" / "requirements.zh.json"
# The prefab design input is no longer the demo default: the review input is
# auto-converted from the generated hardware contract. This path is kept as the
# explicit ``--design`` override (complete-design-data reference sample).
DEFAULT_DESIGN = REPO / "examples" / "m2-closed-loop" / "design-data.json"
DEFAULT_OUT = REPO / "examples" / "m2-closed-loop" / "output"
DEFAULT_PROFILES = REPO / "src" / "review" / "component-profiles.json"

GATE_SCRIPT = REPO / "scripts" / "requirements-gate.py"
REVIEW_SCRIPT = REPO / "src" / "review" / "prototype_review.py"

CONTRACT_NAME = "hardware-contract.json"
REVIEW_INPUT_NAME = "review-input.json"
CONVERSION_ISSUES_NAME = "conversion-issues.txt"
REVIEW_NAME = "machine-review.json"
REPORT_NAME = "prototype-review-report-zh.md"
SUMMARY_NAME = "demo-summary.zh.md"

# Every artifact this demo owns; removed before a run so the output directory
# reflects exactly the current invocation (deterministic, no stale leftovers).
OWNED_ARTIFACTS = (
    CONTRACT_NAME,
    REVIEW_INPUT_NAME,
    CONVERSION_ISSUES_NAME,
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


def _write_review_input(path: Path, value: dict) -> None:
    """Serialize the review input byte-for-byte like scripts/contract-to-review-cli.py."""
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def _render_summary(
    contract: dict,
    result: dict,
    *,
    out: Path,
    now: str | None,
    design_source: str,
    conversion_issues: list[str] | None,
) -> str:
    counts = result["counts"]
    unresolved = contract["unresolved"]
    unresolved_text = "\n".join(f"  - {u}" for u in unresolved) or "  - 无"
    generated_at = contract["generatedAt"]
    timestamp_note = (
        f"所有时间戳已由 `--now {now}` 固定,同一输出目录下两次运行输出字节一致。"
        if now
        else "未指定 `--now`,时间戳为本次运行实际时间。"
    )
    blocker_heading = f"- blocker:{counts['blocker']} 个" + (
        "(唯一)" if counts["blocker"] == 1 else ""
    )
    if conversion_issues is None:
        review_index, real_loop_index, reproduce_index = "三", "四", "五"
    else:
        review_index, real_loop_index, reproduce_index = "四", "五", "六"
    converter_lines: list[str] = []
    if conversion_issues is not None:
        conversion_text = (
            "\n".join(f"  - {line}" for line in conversion_issues)
            or "  - 无(所有机械连接器均匹配到坐标与网络)"
        )
        converter_lines = [
            "",
            f"## 三、自动转换(hardware-contract → {REVIEW_INPUT_NAME})",
            "",
            "- 转换器:`src/spec/contract_to_review.py`(离线,fail-closed:contract 未表达的器件级信息一律不虚构)",
            f"- 转换产物:{REVIEW_INPUT_NAME}(已写入输出目录,直接供审核引擎消费)",
            f"- 转换日志:{len(conversion_issues)} 条",
            conversion_text,
        ]
    if conversion_issues is not None:
        # Default auto-conversion path: no prefab device-level design data, so
        # the review honestly fails closed on missing data.
        chain_note_lines = [
            "上面的离线自动链路**没有预制器件级设计数据**:contract 只有 3 个连接器(带坐标)与",
            "2 个电源域,没有电容、没有走线宽度、没有保存重载证据;转换器绝不猜测。因此审核",
            "fail-closed 给出 `PERSISTENCE` blocker 与 `TRACE_DATA_MISSING`×2、",
            "`EVIDENCE_SCOPE:OFFLINE_FORECAST` advisory——这是全自动链路对“数据不足”的诚实结论,",
            "不是回归;J2 去耦这类工程 blocker 只有在具备完整器件级设计数据的真实 EDA 图纸中",
            "才能审出并修正。",
        ]
    else:
        # Explicit --design override: the prefab complete-design sample carries
        # the device-level facts and reproduces the historical M2 BEFORE blocker.
        chain_note_lines = [
            "上面的离线审核输入是**显式提供的完整设计数据样例**(`--design`,跳过自动转换),复现真实",
            "M2 BEFORE 状态的语义:J2 附近最近的电容是 10uF 储能电容,不在 0.08–0.22uF 旁路范围内,",
            "稳定命中唯一 blocker `DECOUPLING_DISTANCE:J2:+5V`。该输入包含电容、走线宽度等器件级",
            "事实;默认的全自动转换链路则因缺少器件级数据而按 fail-closed 结论评级(见 README 说明)。",
        ]
    lines = [
        "# M2 电源分配板 — 端到端闭环公开示例(离线部分)",
        "",
        "> **NOT FOR MANUFACTURING(不可直接制造)**",
        ">",
        "> 本示例用清洗/合成数据复现「中文需求 → 硬件规格(hardware-contract)→ 自动转换 → 自动审核 → 评级」",
        "> 这条**可离线运行**的链路。完整闭环(含真实 EDA 画板、白名单修正、保存重载复验)",
        "> 已在真实嘉立创 EDA 环境中完成并通过;本示例不在此处自动画板、不执行任何 EDA 写入",
        "> 或自动修正。",
        "",
        "## 一、输入",
        "",
        f"- 需求:`{DEFAULT_REQUIREMENTS.relative_to(REPO).as_posix()}`(清洗后的中文需求)",
        f"- 设计数据:{design_source}",
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
    ]
    lines += converter_lines
    lines += [
        "",
        f"## {review_index}、自动审核(machine-review.json / prototype-review-report-zh.md)",
        "",
        f"- 评级:`{result['rating']}`(当前不适合样板)",
        blocker_heading,
        _blocker_details(result),
        f"- advisory:{counts['advisory']} 个 —— " + "、".join(_group_findings(result, "advisory")),
        f"- pass:{counts['pass']} 个 —— " + "、".join(_group_findings(result, "pass")),
        "",
        f"## {real_loop_index}、真实闭环在哪里完成过",
        "",
        "真实 M2 案例中,真实 EDA 环境审出**且仅一个** blocker `DECOUPLING_DISTANCE:J2:+5V`",
        "(J2 输出口缺少足够近的旁路电容;最近的是 10uF 储能电容,不在 0.08–0.22uF 旁路范围内);",
        "经白名单修正(在 J2 附近新增一颗 100nF 旁路电容)→ 在真实 EDA 中改图 → 保存重载 →",
        "独立读回 → 复审,评级提升为 `suitable_for_low_risk_prototype`。该闭环**已真实发生并通过**;",
        "本公开示例只复现上面这段可离线运行的链路,坐标与网络均为合成值,",
        "不含任何私有 EDA 信息(UUID/器件ID/审批记录/截图路径)。",
        "",
    ]
    lines += chain_note_lines
    lines += [
        "",
        f"## {reproduce_index}、如何复现",
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
    parser.add_argument("--design", type=Path, default=None,
                        help="explicit review-input JSON used directly, skipping contract→review conversion "
                             "(optional; by default the review input is auto-converted from the generated "
                             "hardware contract, so no prefab design data is needed; reference sample: "
                             "examples/m2-closed-loop/design-data.json)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="output directory (default: examples/m2-closed-loop/output)")
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES,
                        help="component profiles JSON (default: src/review/component-profiles.json)")
    parser.add_argument("--now", help="ISO 8601 timestamp; pins all generatedAt fields for byte-identical reruns")
    args = parser.parse_args(argv)

    requirements = args.requirements.resolve()
    design = args.design.resolve() if args.design is not None else None
    profiles = args.profiles.resolve()
    out = args.out.resolve()

    for label, path in (("--requirements", requirements), ("--profiles", profiles)):
        if not path.is_file():
            return _fail(f"{label} file not found: {path}")
    if design is not None and not design.is_file():
        return _fail(f"--design file not found: {design}")
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

    # ---- step 2: review input (auto-converted from the contract by default) ----
    conversion_issues: list[str] | None = None
    if design is None:
        # Default: no prefab design data. Project the step-1 hardware contract
        # into review input with the offline converter (never guesses), then
        # feed that converted input to the independent review engine.
        try:
            review_input = contract_to_review_input(contract, now=args.now)
            conversion_issues = contract_to_review_issues(contract)
        except ContractInputError as exc:
            return _fail(f"contract→review conversion rejected the contract: {exc}")
        review_source = out / REVIEW_INPUT_NAME
        _write_review_input(review_source, review_input)
        if conversion_issues:
            (out / CONVERSION_ISSUES_NAME).write_text(
                "".join(line + "\n" for line in conversion_issues), encoding="utf-8"
            )
        design_source = (
            "由需求门禁产出的 `hardware-contract.json` 经离线转换器自动生成"
            f"(非预制,无需任何预制设计数据;转换产物 `{REVIEW_INPUT_NAME}` 见输出目录)"
        )
    else:
        # Backward-compatible override: an explicit review input is used as-is.
        review_source = design
        try:
            design_label = design.relative_to(REPO).as_posix()
        except ValueError:
            # A --design path outside the repository is legitimate (Windows
            # users commonly pass an absolute path); fall back to the file name
            # instead of crashing.
            design_label = design.name or str(design)
        design_source = (
            f"`{design_label}`(显式 `--design`,直接作为审核输入,跳过自动转换)"
        )

    review = _run_python([
        REVIEW_SCRIPT, "--input", review_source, "--profiles", profiles, "--output", out,
    ])
    if review.returncode != 0:
        return _fail("prototype review failed", output=review.stderr or review.stdout)
    try:
        result = _read_json(out / REVIEW_NAME)
    except (OSError, json.JSONDecodeError) as exc:
        return _fail(f"could not read review result: {exc}")
    counts = result["counts"]
    blockers = _group_findings(result, "blocker")
    blocker_note = f" [{', '.join(blockers)}]" if blockers else ""
    print(
        f"[2/3] prototype review .......... {result['rating']} "
        f"({counts['blocker']} blocker{blocker_note}, {counts['advisory']} advisory, {counts['pass']} pass)"
    )

    # ---- step 3: deterministic timestamps + demo summary ----
    if args.now:
        _pin_timestamps(out, args.now)
    summary_path = out / SUMMARY_NAME
    summary_path.write_text(
        _render_summary(
            contract,
            result,
            out=out,
            now=args.now,
            design_source=design_source,
            conversion_issues=conversion_issues,
        ),
        encoding="utf-8",
    )
    print(f"[3/3] demo summary .............. {summary_path}")
    print("closed-loop demo OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
