#!/usr/bin/env python3
"""Deterministic, read-only Prototype review engine for normalized JLCEDA evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


RATING_UNSUITABLE = "not_suitable_for_prototype"
RATING_FIX_FIRST = "suitable_after_corrections"
RATING_SUITABLE = "suitable_for_low_risk_prototype"

REQUIRED_PROTOTYPE_GATES = (
    "schematicErrors",
    "schematicWarnings",
    "pcbDrcFindings",
    "unroutedNets",
    "containment",
    "savedReloaded",
)

EVIDENCE_ONLY_FINDING_PREFIXES = (
    "EVIDENCE_INCOMPLETE:",
    "EVIDENCE_CONFLICT:",
    "EVIDENCE_SCOPE:",
)

RATING_LABEL_ZH = {
    RATING_UNSUITABLE: "当前不适合样板",
    RATING_FIX_FIRST: "修正后适合低风险样板",
    RATING_SUITABLE: "适合低风险样板",
}

INPUT_SCHEMA = "jlceda-prototype-review-input/1.0"
PROFILE_SCHEMA = "jlceda-component-profiles/1.0"


class InputValidationError(ValueError):
    """Raised when normalized evidence is structurally unsafe to review."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def confidence_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(value, 0)


def _is_absolute_path(value: str) -> bool:
    return bool(
        re.match(r"^[A-Za-z]:[\\/]", value)
        or value.startswith("\\\\")
        or value.startswith("//")
        or value.startswith("/")
        or value.startswith("~/")
        or value.lower().startswith("file://")
    )


def _contains_absolute_path(value: str) -> bool:
    return bool(
        re.search(r"(?i)(?:^|[\s('])(?:[A-Z]:[\\/]|\\\\|file://)", value)
        or re.search(r"(?:^|[\s('])/(?:Users|home|private|tmp|var)/", value)
        or re.search(r"(?:^|[\s('])~/", value)
    )


def _basename_for_public_output(value: str) -> str:
    """Reduce absolute local paths to a portable basename before emitting evidence."""
    if value.lower().startswith("file://"):
        value = value[7:]
    if re.match(r"^[A-Za-z]:[\\/]", value) or value.startswith("\\\\"):
        return PureWindowsPath(value).name or "local-source"
    return PurePosixPath(value.replace("\\", "/")).name or "local-source"


def sanitize_public_value(value: Any) -> Any:
    """Recursively remove absolute workstation paths from generated public artifacts."""
    if isinstance(value, str):
        if _is_absolute_path(value):
            return _basename_for_public_output(value)
        if _contains_absolute_path(value):
            return "local-source"
        return value
    if isinstance(value, list):
        return [sanitize_public_value(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_public_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): sanitize_public_value(item) for key, item in value.items()}
    return value


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputValidationError(f"{label} must be a JSON object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise InputValidationError(f"{label} must be a JSON array")
    return value


def _check_unique_rows(rows: list[Any], key: str, label: str) -> None:
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise InputValidationError(f"{label}[{index}] must be a JSON object")
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise InputValidationError(f"{label}[{index}].{key} must be a non-empty string")
        if value in seen:
            raise InputValidationError(f"duplicate {label}.{key}: {value}")
        seen.add(value)


def validate_design(design: Any) -> dict[str, Any]:
    """Validate the minimum normalized evidence contract without third-party packages."""
    d = _require_mapping(design, "input")
    schema = d.get("schema")
    if schema != INPUT_SCHEMA:
        raise InputValidationError(f"input.schema must equal {INPUT_SCHEMA!r}")
    if not isinstance(d.get("designName"), str) or not d["designName"].strip():
        raise InputValidationError("input.designName must be a non-empty string")
    components = _require_list(d.get("components"), "input.components")
    nets = _require_list(d.get("nets"), "input.nets")
    _require_mapping(d.get("checks"), "input.checks")
    _check_unique_rows(components, "ref", "input.components")
    _check_unique_rows(nets, "name", "input.nets")
    for index, component in enumerate(components):
        if ("x" in component) != ("y" in component):
            raise InputValidationError(f"input.components[{index}] must provide both x and y or neither")
        for coordinate in ("x", "y"):
            if coordinate in component and not isinstance(component[coordinate], (int, float)):
                raise InputValidationError(f"input.components[{index}].{coordinate} must be numeric")
        if "nets" in component and not isinstance(component["nets"], list):
            raise InputValidationError(f"input.components[{index}].nets must be a JSON array")
        if len(component.get("nets", [])) != len(set(component.get("nets", []))):
            raise InputValidationError(f"input.components[{index}].nets must not contain duplicates")
    if "sourceEvidence" in d:
        evidence = _require_list(d["sourceEvidence"], "input.sourceEvidence")
        if any(not isinstance(item, str) for item in evidence):
            raise InputValidationError("input.sourceEvidence items must be strings")
    return d


def validate_profiles(profiles: Any) -> dict[str, Any]:
    data = _require_mapping(profiles, "profiles")
    if data.get("schema") != PROFILE_SCHEMA:
        raise InputValidationError(f"profiles.schema must equal {PROFILE_SCHEMA!r}")
    rows = data.get("profiles")
    if not isinstance(rows, dict):
        raise InputValidationError("profiles.profiles must be a JSON object")
    for key, profile in rows.items():
        if not isinstance(key, str) or not key or not isinstance(profile, dict):
            raise InputValidationError("each component profile must have a string key and object value")
        if not isinstance(profile.get("kind"), str) or not profile["kind"]:
            raise InputValidationError(f"profile {key!r} must have a non-empty kind")
        source = _require_mapping(profile.get("source"), f"profile {key!r}.source")
        for field in ("manufacturer", "title", "confidence", "redistribution"):
            if not isinstance(source.get(field), str) or not source[field]:
                raise InputValidationError(f"profile {key!r}.source.{field} must be a non-empty string")
        if source["confidence"] not in {"low", "medium", "high"}:
            raise InputValidationError(f"profile {key!r}.source.confidence must be low, medium or high")
    return data


@dataclass
class Finding:
    id: str
    severity: str
    confidence: str
    title: str
    riskZh: str
    locations: list[str]
    evidence: list[dict[str, Any]]
    calculation: str
    recommendationZh: str
    revalidation: str
    unresolvedAssumptions: list[str]
    ruleFamily: str


class Review:
    def __init__(self, design: dict[str, Any], profiles: dict[str, Any]):
        self.d = design
        self.profiles = profiles.get("profiles", profiles)
        self.findings: list[Finding] = []
        self.components = {c["ref"]: c for c in design.get("components", [])}
        self.nets = {n["name"]: n for n in design.get("nets", [])}
        self.evidence_completeness: dict[str, Any] = {
            "status": "incomplete",
            "requiredFields": list(REQUIRED_PROTOTYPE_GATES),
            "missingFields": [],
            "invalidFields": [],
            "contradictions": [],
            "scopeLimitations": [],
            "gates": {field: "missing" for field in REQUIRED_PROTOTYPE_GATES},
            "allRequiredEvidencePresentAndValid": False,
            "allPrototypeGatesPassed": False,
        }

    def profile(self, component: dict[str, Any]) -> dict[str, Any] | None:
        key = component.get("profile")
        return self.profiles.get(key) if key else None

    def add(self, **kwargs: Any) -> None:
        self.findings.append(Finding(**kwargs))

    def evidence_for(self, profile: dict[str, Any] | None, fields: list[str]) -> list[dict[str, Any]]:
        if not profile:
            return []
        source = profile.get("source", {})
        return [{
            "source": source.get("file") or source.get("url") or "profile",
            "pageOrTable": source.get("pageOrTable"),
            "fields": {k: profile.get(k) for k in fields if k in profile},
            "sourceConfidence": source.get("confidence", "low"),
        }]

    def run(self) -> dict[str, Any]:
        self.rule_identity_and_profiles()
        self.rule_power_paths()
        self.rule_regulator_thermal()
        self.rule_fuses()
        self.rule_hbridges()
        self.rule_trace_capacity()
        self.rule_decoupling_and_bulk()
        self.rule_interfaces()
        self.rule_debug_and_usability()
        self.rule_schematic_and_pcb_gates()
        self.rule_ground_and_topology()
        self.rule_firmware_pins()
        return self.result()

    def rule_identity_and_profiles(self) -> None:
        for c in self.components.values():
            p = self.profile(c)
            if not p and c.get("critical", False):
                self.add(
                    id=f"DATASHEET_MISSING:{c['ref']}", severity="advisory", confidence="high",
                    title="关键器件缺少可核验能力数据", riskZh="额定值、封装或引脚证据不足，样板结论需要保守处理。",
                    locations=[c["ref"]], evidence=[{"component": c.get("mpn") or c.get("value")}],
                    calculation="critical component has no component profile",
                    recommendationZh="补充厂商数据手册、精确 MPN、封装和 pin-to-pad 证据。",
                    revalidation="重新加载 component profile 并运行身份、额定值和 pin-to-pad 规则。",
                    unresolvedAssumptions=["器件能力和封装来源未闭合"], ruleFamily="identity")
                continue
            if not p:
                continue
            supported = p.get("supportedPackages")
            package = c.get("package")
            if supported and package and package not in supported:
                self.add(
                    id=f"PACKAGE_UNSUPPORTED:{c['ref']}", severity="blocker", confidence="high",
                    title="器件型号与 PCB 封装证据不一致", riskZh="采购器件可能装不上、方向错误或引脚不匹配，存在上电损坏风险。",
                    locations=[c["ref"], package], evidence=self.evidence_for(p, ["supportedPackages"]),
                    calculation=f"observed package={package}; supported={supported}",
                    recommendationZh="锁定精确厂商 MPN，并改用数据手册支持且 pin-to-pad 已核验的封装。",
                    revalidation="精确比对 MPN、symbol、footprint、pin names、pad numbers。",
                    unresolvedAssumptions=[], ruleFamily="identity")

    def rule_power_paths(self) -> None:
        for path in self.d.get("powerPaths", []):
            regulator = self.components.get(path.get("regulatorRef"))
            if not regulator:
                continue
            p = self.profile(regulator)
            if not p:
                continue
            vin_min = float(path["sourceMinV"])
            drops = []
            for ref in path.get("seriesRefs", []):
                comp = self.components.get(ref)
                cp = self.profile(comp) if comp else None
                drop = float((cp or {}).get("forwardDropV", comp.get("forwardDropV", 0) if comp else 0))
                drops.append((ref, drop))
                vin_min -= drop
            output = float(p.get("outputV", path.get("outputV", 0)))
            dropout = float(p.get("dropoutMaxV", p.get("dropoutTypicalV", 0)))
            margin = vin_min - output - dropout
            ev = self.evidence_for(p, ["outputV", "dropoutTypicalV", "dropoutMaxV"])
            ev.append({"sourceMinV": path["sourceMinV"], "seriesDropsV": drops})
            if margin < 0:
                self.add(
                    id=f"POWER_HEADROOM:{regulator['ref']}", severity="blocker", confidence="high",
                    title="最低输入电压不足以维持稳压输出", riskZh="低电量或低输入电压时电源轨会下降，系统可能不启动、复位或外设异常。",
                    locations=[regulator["ref"], path.get("inputNet", ""), path.get("outputNet", "")], evidence=ev,
                    calculation=f"{path['sourceMinV']:.3g}V - series {sum(v for _, v in drops):.3g}V - {output:.3g}V - dropout {dropout:.3g}V = {margin:.3g}V",
                    recommendationZh="选择覆盖完整输入范围的稳压方案，或提高输入下限并保留全温、全负载压差裕量。",
                    revalidation="对 VIN(min/max)、串联压降、dropout 和负载边界重新计算，并在边界电压实测输出最低值。",
                    unresolvedAssumptions=path.get("assumptions", []), ruleFamily="power")
            else:
                self.add(
                    id=f"POWER_HEADROOM_PASS:{regulator['ref']}", severity="pass", confidence="high",
                    title="最低输入电压压差裕量通过", riskZh="最低输入条件仍保留稳压余量。",
                    locations=[regulator["ref"]], evidence=ev, calculation=f"headroom margin={margin:.3g}V",
                    recommendationZh="保持当前输入范围与器件额定值绑定。", revalidation="边界电压负载测试。",
                    unresolvedAssumptions=path.get("assumptions", []), ruleFamily="power")
            source_max = path.get("sourceMaxV")
            max_vin = p.get("maxInputV")
            if source_max is not None and max_vin is not None:
                max_at_reg = float(source_max) - sum(v for _, v in drops)
                if max_at_reg > float(max_vin):
                    self.add(
                        id=f"ABS_MAX_INPUT:{regulator['ref']}", severity="blocker", confidence="high",
                        title="稳压器输入超过绝对最大额定值", riskZh="高输入条件可能造成器件永久损坏。",
                        locations=[regulator["ref"]], evidence=self.evidence_for(p, ["maxInputV"]),
                        calculation=f"max at input={max_at_reg:.3g}V > max={max_vin}V",
                        recommendationZh="降低输入上限或选用更高额定器件。", revalidation="最大输入及瞬态钳位复算。",
                        unresolvedAssumptions=[], ruleFamily="power")

    def rule_fuses(self) -> None:
        for circuit in self.d.get("protectedCircuits", []):
            fuse = self.components.get(circuit.get("fuseRef"))
            if not fuse:
                continue
            p = self.profile(fuse)
            if not p:
                continue
            continuous = float(circuit.get("continuousCurrentA", 0))
            surge = float(circuit.get("surgeCurrentA", continuous))
            hold = float(p.get("holdCurrentA", 0))
            trip = float(p.get("tripCurrentA", 0))
            derating = float(circuit.get("holdDerating", 0.8))
            usable_hold = hold * derating
            if continuous > usable_hold:
                self.add(
                    id=f"FUSE_HOLD:{fuse['ref']}", severity="blocker", confidence="high",
                    title="保护器件保持电流低于正常负载预算", riskZh="正常启动或运行时保护器件可能升阻或动作，引起掉电和复位。",
                    locations=[fuse["ref"]], evidence=self.evidence_for(p, ["holdCurrentA", "tripCurrentA"]),
                    calculation=f"continuous={continuous:.3g}A > derated hold={hold:.3g}×{derating:.2g}={usable_hold:.3g}A; surge={surge:.3g}A; trip={trip:.3g}A",
                    recommendationZh="依据持续、启动、堵转电流和温度降额重新选择保险丝或 PTC。",
                    revalidation="加载实际负载曲线并验证正常启动不动作、故障场景按预期保护。",
                    unresolvedAssumptions=circuit.get("assumptions", []), ruleFamily="protection")
            elif surge >= trip:
                self.add(
                    id=f"FUSE_SURGE:{fuse['ref']}", severity="advisory", confidence="high",
                    title="启动浪涌可能进入保护器件动作区", riskZh="启动可靠性取决于浪涌持续时间和器件动作曲线。",
                    locations=[fuse["ref"]], evidence=self.evidence_for(p, ["holdCurrentA", "tripCurrentA"]),
                    calculation=f"surge={surge:.3g}A >= trip reference={trip:.3g}A",
                    recommendationZh="核验时间-电流曲线并进行启动脉冲测试。", revalidation="记录浪涌波形并与动作曲线叠加。",
                    unresolvedAssumptions=circuit.get("assumptions", []), ruleFamily="protection")
            else:
                self.add(
                    id=f"FUSE_PASS:{fuse['ref']}", severity="pass", confidence="high", title="保护器件电流预算通过",
                    riskZh="正常负载和浪涌均低于当前保护预算。", locations=[fuse["ref"]],
                    evidence=self.evidence_for(p, ["holdCurrentA", "tripCurrentA"]),
                    calculation=f"continuous={continuous:.3g}A <= derated hold={usable_hold:.3g}A; surge={surge:.3g}A < trip={trip:.3g}A",
                    recommendationZh="保留温度降额和动作曲线证据。", revalidation="负载脉冲测试。", unresolvedAssumptions=[], ruleFamily="protection")

    def rule_regulator_thermal(self) -> None:
        for use in self.d.get("regulatorUses", []):
            comp = self.components.get(use.get("regulatorRef"))
            if not comp:
                continue
            p = self.profile(comp)
            if not p:
                continue
            vin = float(use["inputMaxV"])
            vout = float(p.get("outputV", use.get("outputV", 0)))
            load = float(use["loadMaxA"])
            loss = max(0.0, (vin - vout) * load)
            theta = float(p.get("thermalResistanceCPerW", use.get("thermalResistanceCPerW", 0)))
            rise = loss * theta if theta else None
            recommended = p.get("recommendedMaxDissipationW", use.get("recommendedMaxDissipationW"))
            caution_rise = float(use.get("cautionRiseC", 50))
            blocker_rise = float(use.get("blockerRiseC", 80))
            severity = "pass"
            if recommended is not None and loss > float(recommended):
                severity = "blocker"
            elif rise is None:
                severity = "advisory"
            elif rise > blocker_rise:
                severity = "blocker"
            elif rise > caution_rise:
                severity = "advisory"
            self.add(
                id=f"REGULATOR_THERMAL:{comp['ref']}", severity=severity, confidence=use.get("confidence", "medium"),
                title="稳压器功耗/温升预算" + ("超限" if severity == "blocker" else ("需要核验" if severity == "advisory" else "通过")),
                riskZh="线性稳压器在高输入和负载下会把压差变为热量，可能过热、降额或使输出失稳。" if severity != "pass" else "配置负载下稳压器损耗和估算温升在门限内。",
                locations=[comp["ref"]], evidence=self.evidence_for(p, ["outputV", "thermalResistanceCPerW", "recommendedMaxDissipationW"]),
                calculation=f"P=({vin:.3g}V-{vout:.3g}V)×{load:.3g}A={loss:.3g}W; ΔT={'unknown' if rise is None else f'{rise:.3g}°C'}",
                recommendationZh="绑定最终 MPN、封装铜面积和环境温度；降低压差/负载或换用效率更高的稳压方案。",
                revalidation="以输入上限和最大负载重算，随后实测稳压器温度与输出稳定性。",
                unresolvedAssumptions=use.get("assumptions", []), ruleFamily="regulator_thermal")

    def rule_hbridges(self) -> None:
        for use in self.d.get("hbridgeUses", []):
            comp = self.components.get(use.get("driverRef"))
            if not comp:
                continue
            p = self.profile(comp)
            if not p:
                continue
            run = float(use["perChannelRunA"])
            peak = float(use.get("perChannelPeakA", run))
            channels = int(use.get("channelsUsed", 1))
            continuous_max = float(p.get("continuousCurrentPerChannelA", 0))
            peak_max = float(p.get("peakCurrentPerChannelA", 0))
            bridge_drop = float(p.get("bridgeDropAtRatedV", 0))
            loss = channels * run * bridge_drop
            theta = float(p.get("thetaJaCPerW", 0))
            rise = loss * theta
            allowed_rise = float(use.get("maxEstimatedRiseC", 60))
            blocker = run > continuous_max + 1e-12 or peak > peak_max + 1e-12 or rise > allowed_rise + 1e-12
            severity = "blocker" if blocker else ("advisory" if rise > allowed_rise * 0.65 else "pass")
            self.add(
                id=f"HBRIDGE_THERMAL:{comp['ref']}", severity=severity, confidence="high",
                title="H 桥电流、压降与热预算" + ("超限" if blocker else "通过"),
                riskZh="驱动压降会降低负载电压，过高损耗会造成过热或热保护。" if severity != "pass" else "驱动电流和估算温升在配置门限内。",
                locations=[comp["ref"]], evidence=self.evidence_for(p, ["continuousCurrentPerChannelA", "peakCurrentPerChannelA", "bridgeDropAtRatedV", "thetaJaCPerW"]),
                calculation=f"run={run:.3g}A/ch (limit {continuous_max:.3g}); peak={peak:.3g}A/ch (limit {peak_max:.3g}); loss={channels}×{run:.3g}×{bridge_drop:.3g}={loss:.3g}W; rise={loss:.3g}×{theta:.3g}={rise:.3g}°C",
                recommendationZh="使用与实际持续/堵转电流匹配的低损耗驱动器，或提供散热铜、环境温度和温升实测证据。",
                revalidation="以实际负载电流重算损耗并记录满载及短时堵转温度和负载端电压。",
                unresolvedAssumptions=use.get("assumptions", []), ruleFamily="driver")

    @staticmethod
    def ipc2221_capacity(width_mm: float, copper_oz: float, delta_c: float) -> float:
        width_mil = width_mm / 0.0254
        thickness_mil = 1.378 * copper_oz
        area_mil2 = width_mil * thickness_mil
        return 0.048 * (delta_c ** 0.44) * (area_mil2 ** 0.725)

    def rule_trace_capacity(self) -> None:
        settings = self.d.get("pcb", {}).get("traceCapacity", {})
        copper_oz = float(settings.get("copperOz", 1.0))
        delta_c = float(settings.get("allowedRiseC", 10.0))
        margin = float(settings.get("currentMargin", 1.25))
        for n in self.nets.values():
            if n.get("role") not in {"power", "motor", "high_current_return"}:
                continue
            width = n.get("minWidthMm")
            current = n.get("designCurrentA")
            if width is None or current is None:
                self.add(
                    id=f"TRACE_DATA_MISSING:{n['name']}", severity="advisory", confidence="high",
                    title="功率网络缺少线宽或电流约束", riskZh="线路压降和温升风险没有量化。", locations=[n["name"]],
                    evidence=[{"widthMm": width, "designCurrentA": current}], calculation="required inputs missing",
                    recommendationZh="补充铜厚、最小线宽、neck-down、过孔与运行/浪涌电流。",
                    revalidation="执行功率网电流密度和压降检查。", unresolvedAssumptions=["功率网络参数不完整"], ruleFamily="pcb_power")
                continue
            capacity = self.ipc2221_capacity(float(width), copper_oz, delta_c)
            required = float(current) * margin
            if capacity < required:
                self.add(
                    id=f"TRACE_CAPACITY:{n['name']}", severity="blocker", confidence="medium",
                    title="功率走线电流裕量不足", riskZh="启动或故障电流可能造成明显压降和局部发热。",
                    locations=[n["name"]], evidence=[{"minWidthMm": width, "copperOz": copper_oz, "allowedRiseC": delta_c, "designCurrentA": current}],
                    calculation=f"IPC-2221 conservative estimate={capacity:.3g}A < required {current:.3g}×{margin:.2g}={required:.3g}A",
                    recommendationZh="按实际铜厚、电流、允许温升和压降加宽、铺铜并消除长 neck-down；核验过孔并联能力。",
                    revalidation="重新提取全路径最小线宽、neck-down 和过孔，复算并做满载压降/热测试。",
                    unresolvedAssumptions=["IPC-2221 是保守估算，最终以板厂叠层和实测为准"], ruleFamily="pcb_power")
            else:
                self.add(
                    id=f"TRACE_PASS:{n['name']}", severity="pass", confidence="medium", title="功率走线估算通过",
                    riskZh="当前线宽在配置的温升和电流裕量下通过保守估算。", locations=[n["name"]],
                    evidence=[{"minWidthMm": width, "capacityA": capacity, "requiredA": required}], calculation=f"{capacity:.3g}A >= {required:.3g}A",
                    recommendationZh="仍需检查 neck-down、过孔和实际压降。", revalidation="满载压降和温升测试。",
                    unresolvedAssumptions=["估算依赖铜厚和环境"], ruleFamily="pcb_power")

    def find_caps(self, req: dict[str, Any]) -> list[tuple[dict[str, Any], float]]:
        target = self.components.get(req["targetRef"])
        out = []
        if not target:
            return out
        for c in self.components.values():
            uf = c.get("capacitanceUf")
            if uf is None:
                continue
            nets = set(c.get("nets", []))
            if {req["supplyNet"], req.get("returnNet", "GND")} <= nets and "x" in c and "y" in c:
                out.append((c, distance(c, target)))
        return out

    def rule_decoupling_and_bulk(self) -> None:
        for req in self.d.get("decouplingRequirements", []):
            caps = self.find_caps(req)
            min_uf = float(req.get("minCapacitanceUf", 0))
            max_uf = float(req.get("maxCapacitanceUf", float("inf")))
            max_distance = float(req.get("maxDistanceMm", 5))
            matching = [(c, d) for c, d in caps if min_uf <= float(c["capacitanceUf"]) <= max_uf and d <= max_distance]
            if not matching:
                nearest = min(caps, key=lambda x: x[1]) if caps else None
                self.add(
                    id=f"DECOUPLING_DISTANCE:{req['targetRef']}:{req['supplyNet']}", severity=req.get("severity", "blocker"), confidence="high",
                    title="关键电源脚缺少足够近的去耦电容", riskZh="负载切换时电源脚可能出现跌落或尖峰，引起复位、通信异常或误动作。",
                    locations=[req["targetRef"], req["supplyNet"]] + ([nearest[0]["ref"]] if nearest else []),
                    evidence=[{"requiredUfRange": [min_uf, None if math.isinf(max_uf) else max_uf], "maxDistanceMm": max_distance, "nearest": {"ref": nearest[0]["ref"], "distanceMm": round(nearest[1], 3), "capacitanceUf": nearest[0]["capacitanceUf"]} if nearest else None}],
                    calculation="no capacitor satisfies value, net pairing and geometric distance together",
                    recommendationZh="把符合器件数据手册的去耦电容放到电源脚与回流脚附近，缩短高频回路。",
                    revalidation="从 PCB 坐标重新计算电容到目标电源脚/器件的距离，并验证网络和值。",
                    unresolvedAssumptions=req.get("assumptions", []), ruleFamily="decoupling")
            else:
                c, d = min(matching, key=lambda x: x[1])
                self.add(
                    id=f"DECOUPLING_PASS:{req['targetRef']}:{req['supplyNet']}", severity="pass", confidence="high", title="去耦配置通过",
                    riskZh="存在满足容量、网络和距离要求的本地电容。", locations=[req["targetRef"], c["ref"]],
                    evidence=[{"capacitanceUf": c["capacitanceUf"], "distanceMm": round(d, 3)}], calculation=f"{d:.3g}mm <= {max_distance:.3g}mm",
                    recommendationZh="保持紧凑回路。", revalidation="保存重载后重复几何检查。", unresolvedAssumptions=[], ruleFamily="decoupling")
        for req in self.d.get("bulkCapRequirements", []):
            caps = self.find_caps(req)
            min_uf = float(req["minCapacitanceUf"])
            max_distance = float(req.get("maxDistanceMm", 15))
            matching = [(c, d) for c, d in caps if float(c["capacitanceUf"]) >= min_uf and d <= max_distance]
            if not matching:
                self.add(
                    id=f"BULK_CAP:{req['targetRef']}:{req['supplyNet']}", severity=req.get("severity", "blocker"), confidence="high",
                    title="动态负载附近缺少储能电容", riskZh="启动、PWM 或换向瞬间可能拉低电源并干扰逻辑电路。",
                    locations=[req["targetRef"], req["supplyNet"]], evidence=[{"requiredUf": min_uf, "maxDistanceMm": max_distance, "candidates": [{"ref": c["ref"], "uf": c["capacitanceUf"], "distanceMm": round(d, 2)} for c, d in caps]}],
                    calculation="no local capacitor meets bulk capacitance and distance requirement",
                    recommendationZh="按负载脉冲和允许电压跌落计算储能，并在功率器件电源/回流附近放置低 ESR 电容。",
                    revalidation="重算 C≥I×Δt/ΔV，并从 PCB 坐标验证容量、距离和回路。", unresolvedAssumptions=req.get("assumptions", []), ruleFamily="bulk")
            else:
                c, d = min(matching, key=lambda x: x[1])
                self.add(
                    id=f"BULK_PASS:{req['targetRef']}:{req['supplyNet']}", severity="pass", confidence="high", title="本地储能电容通过",
                    riskZh="动态负载附近存在满足配置门限的储能。", locations=[req["targetRef"], c["ref"]], evidence=[{"uf": c["capacitanceUf"], "distanceMm": round(d, 2)}],
                    calculation=f"{c['capacitanceUf']}uF >= {min_uf}uF and {d:.3g}mm <= {max_distance}mm",
                    recommendationZh="用示波器确认瞬态跌落。", revalidation="动态负载实测。", unresolvedAssumptions=[], ruleFamily="bulk")

    def rule_interfaces(self) -> None:
        for iface in self.d.get("voltageDividers", []):
            vin = float(iface["inputMaxV"])
            top = float(iface["topOhm"])
            bottom = float(iface["bottomOhm"])
            vout = vin * bottom / (top + bottom)
            abs_max = float(iface["receiverAbsMaxV"])
            required_margin = float(iface.get("requiredMarginV", 0.2))
            margin = abs_max - vout
            if vout > abs_max:
                severity = "blocker"
            elif margin < required_margin:
                severity = "advisory"
            else:
                severity = "pass"
            self.add(
                id=f"LEVEL_MARGIN:{iface['id']}", severity=severity, confidence=iface.get("confidence", "high"),
                title="接口电平超限" if severity == "blocker" else ("接口电平裕量偏小" if severity == "advisory" else "接口电平通过"),
                riskZh="输入高电平接近或超过接收器限制，容差和瞬态可能造成异常或损坏。" if severity != "pass" else "分压后电平保留了配置裕量。",
                locations=iface.get("locations", [iface["id"]]), evidence=[{"inputMaxV": vin, "topOhm": top, "bottomOhm": bottom, "receiverAbsMaxV": abs_max}],
                calculation=f"Vout={vin:.3g}×{bottom:.3g}/({top:.3g}+{bottom:.3g})={vout:.3g}V; margin={margin:.3g}V",
                recommendationZh="调整分压或采用明确的电平转换/钳位，并按最高输出、电阻容差和接收器额定值复算。",
                revalidation="最高输入、电阻容差、温度和接收器 VIH/VIL/绝对最大值联合检查。",
                unresolvedAssumptions=iface.get("assumptions", []), ruleFamily="interface")

    def rule_debug_and_usability(self) -> None:
        debug = self.d.get("debugInterface")
        if debug:
            required = set(debug.get("requiredSignals", []))
            present = set(debug.get("presentSignals", []))
            missing = sorted(required - present)
            if missing:
                self.add(
                    id="DEBUG_SIGNALS", severity="advisory", confidence="high", title="调试接口缺少关键恢复信号",
                    riskZh="固件异常、低功耗或调试脚配置错误时，现场恢复和量产调试会更困难。", locations=debug.get("locations", []),
                    evidence=[{"required": sorted(required), "present": sorted(present), "missing": missing}], calculation=f"missing={missing}",
                    recommendationZh="采用标准调试接口或补充缺失的复位/供电参考信号。", revalidation="按调试器线缆针序自动比对。",
                    unresolvedAssumptions=[], ruleFamily="debug")
            else:
                self.add(
                    id="DEBUG_PASS", severity="pass", confidence="high", title="调试接口信号完整", riskZh="配置的调试和恢复信号均存在。",
                    locations=debug.get("locations", []), evidence=[{"present": sorted(present)}], calculation="all required signals present",
                    recommendationZh="保持针序和电压丝印。", revalidation="实物连接调试器。", unresolvedAssumptions=[], ruleFamily="debug")
        usability = self.d.get("usability", {})
        missing_tp = usability.get("missingTestpointNets", [])
        if missing_tp:
            self.add(
                id="TESTPOINTS", severity="advisory", confidence="high", title="关键网络缺少测试点", riskZh="首板上电和故障定位需要夹线或直接碰焊盘，调试风险较高。",
                locations=missing_tp, evidence=[{"missingTestpointNets": missing_tp}], calculation=f"{len(missing_tp)} required nets lack test points",
                recommendationZh="增加可探测的电源、地和关键控制信号测试点。", revalidation="从 PCB 读回测试点及其网络和探针净空。",
                unresolvedAssumptions=[], ruleFamily="usability")
        missing_labels = usability.get("missingSilkscreenLabels", [])
        if missing_labels:
            self.add(
                id="SILKSCREEN", severity="advisory", confidence="high", title="接口丝印信息不足", riskZh="装配或插线时容易接反电源、方向或 Pin 1。",
                locations=missing_labels, evidence=[{"missingLabels": missing_labels}], calculation=f"{len(missing_labels)} label groups missing",
                recommendationZh="补充 Pin 1、极性、电压、接口名和信号方向。", revalidation="截图与 PCB 文字对象自动检查。",
                unresolvedAssumptions=[], ruleFamily="usability")
        antenna = usability.get("antennaKeepout")
        if antenna and not antenna.get("verified", False):
            self.add(
                id="ANTENNA_KEEPOUT", severity="advisory", confidence=antenna.get("confidence", "medium"), title="无线模块天线净空未验证",
                riskZh="铜、金属或线束靠近天线会降低距离和连接稳定性。", locations=antenna.get("locations", []),
                evidence=[antenna], calculation="antenna keepout verification is absent",
                recommendationZh="绑定具体模块机械图并保持天线区无铜、无金属和无高噪声走线。", revalidation="机械叠图与铜层净空检查。",
                unresolvedAssumptions=antenna.get("assumptions", []), ruleFamily="mechanical")

    def rule_schematic_and_pcb_gates(self) -> None:
        checks_value = self.d.get("checks", {})
        checks = checks_value if isinstance(checks_value, dict) else {}
        completeness = self.evidence_completeness
        gates = completeness["gates"]

        evidence_labels = {
            "schematicErrors": ("SCHEMATIC_ERRORS", "原理图错误计数", "固定 ERC"),
            "schematicWarnings": ("SCHEMATIC_WARNINGS", "原理图警告计数", "固定 ERC 逐项明细"),
            "pcbDrcFindings": ("PCB_DRC", "PCB DRC 问题计数", "固定 PCB DRC"),
            "unroutedNets": ("UNROUTED", "未布通网络计数", "PCB 连通性检查"),
            "containment": ("CONTAINMENT", "板框包含检查", "所有 PCB 对象的板框包含检查"),
            "savedReloaded": ("PERSISTENCE", "保存、关闭、重载及独立读回", "保存重载后的对象、网络和摘要比对"),
        }

        def incomplete(field: str, reason: str, observed: Any = None) -> None:
            fid_suffix, label, recheck = evidence_labels[field]
            target = completeness["missingFields"] if reason == "missing" else completeness["invalidFields"]
            target.append(field)
            gates[field] = "missing" if reason == "missing" else "invalid"
            evidence = {"field": f"checks.{field}", "status": reason}
            if reason != "missing":
                evidence.update({"observedType": type(observed).__name__, "observedValue": observed})
            self.add(
                id=f"EVIDENCE_INCOMPLETE:{fid_suffix}", severity="advisory", confidence="high",
                title=f"缺少可信的{label}证据",
                riskZh=f"{label}未明确提供且通过时，默认值会把尚未执行的检查伪装成已通过。",
                locations=[f"checks.{field}"], evidence=[evidence], calculation=f"checks.{field}={reason}",
                recommendationZh=f"从当前真实 EDA 文档采集{label}，保留原始结果并明确记录字段类型。",
                revalidation=f"保存重载后重新执行{recheck}，确认结果明确存在、类型正确且通过。",
                unresolvedAssumptions=[], ruleFamily="evidence_gate",
            )

        count_gates = [
            ("schematicErrors", "SCHEMATIC_ERRORS", "原理图存在错误", "关键连接或电气规则错误可能导致功能失效。"),
            ("pcbDrcFindings", "PCB_DRC", "PCB DRC 存在问题", "几何或电气间距问题尚未闭合。"),
            ("unroutedNets", "UNROUTED", "PCB 存在未布通网络", "相应功能在实物上不会导通。"),
        ]
        for field, fid, title, risk in count_gates:
            if field not in checks:
                incomplete(field, "missing")
                continue
            count = checks[field]
            if type(count) is not int or count < 0:
                incomplete(field, "invalid_type" if type(count) is not int else "invalid_value", count)
                continue
            gates[field] = "pass" if count == 0 else "fail"
            if count:
                self.add(id=fid, severity="blocker", confidence="high", title=title, riskZh=risk, locations=[], evidence=[{"count": count}], calculation=f"count={count}",
                         recommendationZh="逐项修正并保存重载后复查。", revalidation="重新运行固定 ERC/DRC/连通性检查。", unresolvedAssumptions=[], ruleFamily="eda_gate")

        warning_field = "schematicWarnings"
        if warning_field not in checks:
            incomplete(warning_field, "missing")
        else:
            warnings = checks[warning_field]
            if type(warnings) is not int or warnings < 0:
                incomplete(warning_field, "invalid_type" if type(warnings) is not int else "invalid_value", warnings)
            elif warnings == 0:
                gates[warning_field] = "pass"
            else:
                details_available = checks.get("schematicWarningDetailsAvailable") is True
                disposition = checks.get("schematicWarningDisposition")
                explained = details_available and disposition == "explained_and_accepted"
                gates[warning_field] = "explained" if explained else "unexplained"
                if not explained:
                    self.add(id="SCHEMATIC_WARNINGS", severity="advisory", confidence="high", title="原理图警告尚未逐项解释并接受", riskZh="汇总警告可能包含悬空输入、未驱动网络或电源标记问题；只有明细存在并经受控处置后才可通过。",
                             locations=[], evidence=[{"count": warnings, "detailsAvailable": details_available, "disposition": disposition}], calculation=f"warnings={warnings}; explained={explained}",
                             recommendationZh="获取逐项明细，修正问题；确属可接受项时记录解释和受支持的处置状态。", revalidation="重新运行固定 ERC 并逐项核对明细与处置记录。",
                             unresolvedAssumptions=[] if details_available else ["当前证据只有 warning 汇总"], ruleFamily="eda_gate")

        for field in ("containment", "savedReloaded"):
            if field not in checks:
                incomplete(field, "missing")
                continue
            value = checks[field]
            if type(value) is not bool:
                incomplete(field, "invalid_type", value)
                continue
            gates[field] = "pass" if value else "fail"
            if field == "containment" and value is False:
                self.add(id="CONTAINMENT", severity="blocker", confidence="high", title="PCB 对象超出板框", riskZh="板外器件、焊盘或铜会造成机械和制造错误。",
                         locations=[], evidence=[{"containment": False}], calculation="containment=false", recommendationZh="把所有对象移入板框并保留边缘净距。",
                         revalidation="重新执行器件、焊盘、走线、过孔、铜皮和丝印包含检查。", unresolvedAssumptions=[], ruleFamily="pcb_geometry")
            if field == "savedReloaded" and value is False:
                self.add(id="PERSISTENCE", severity="blocker", confidence="high", title="保存重载持久性未通过", riskZh="关闭后设计可能丢失或状态不一致。", locations=[],
                         evidence=[{"savedReloaded": False}], calculation="persistence verification failed", recommendationZh="完成保存、关闭重开和独立读回。",
                         revalidation="保存重载后比较对象、网络和 digest。", unresolvedAssumptions=[], ruleFamily="eda_gate")

        metadata_value = self.d.get("fixtureMetadata", {})
        metadata = metadata_value if isinstance(metadata_value, dict) else {}
        saved_reloaded = checks.get("savedReloaded") if type(checks.get("savedReloaded")) is bool else None
        live_verified = metadata.get("liveEdaVerified")
        persistence_included = metadata.get("persistenceEvidenceIncluded")
        contradictions: list[str] = []
        if saved_reloaded is True and live_verified is False:
            contradictions.append("checks.savedReloaded=true 与 fixtureMetadata.liveEdaVerified=false 冲突")
            self.add(id="EVIDENCE_CONFLICT:LIVE_EDA", severity="advisory", confidence="high", title="保存重载结论与实时 EDA 标记矛盾",
                     riskZh="离线fixture声称已经保存重载，会把工程预测误写成当前设计已验证。", locations=["checks.savedReloaded", "fixtureMetadata.liveEdaVerified"],
                     evidence=[{"savedReloaded": True, "liveEdaVerified": False}], calculation="savedReloaded=true AND liveEdaVerified=false",
                     recommendationZh="把离线预测与实时审核结果分开；只在真实 EDA 保存、关闭、重载和独立读回后标记通过。",
                     revalidation="在目标 EDA 文档完成保存重载闭环并重新采集元数据。", unresolvedAssumptions=[], ruleFamily="evidence_gate")
        if saved_reloaded is True and persistence_included is False:
            contradictions.append("checks.savedReloaded=true 与 fixtureMetadata.persistenceEvidenceIncluded=false 冲突")
            self.add(id="EVIDENCE_CONFLICT:PERSISTENCE", severity="advisory", confidence="high", title="保存重载结论缺少对应持久化证据",
                     riskZh="没有保存重载证据包时，成功标记不能证明新增或修改对象在关闭后仍存在。", locations=["checks.savedReloaded", "fixtureMetadata.persistenceEvidenceIncluded"],
                     evidence=[{"savedReloaded": True, "persistenceEvidenceIncluded": False}], calculation="savedReloaded=true AND persistenceEvidenceIncluded=false",
                     recommendationZh="附上保存前、重载后和独立读回的最小脱敏证据，再声明持久化通过。",
                     revalidation="核对重载前后对象、网络和摘要一致，并验证证据清单哈希。", unresolvedAssumptions=[], ruleFamily="evidence_gate")
        completeness["contradictions"] = contradictions
        if live_verified is False and not contradictions:
            completeness["scopeLimitations"].append("fixtureMetadata.liveEdaVerified=false")
            self.add(id="EVIDENCE_SCOPE:OFFLINE_FORECAST", severity="advisory", confidence="high", title="当前结果仅是离线工程预测",
                     riskZh="离线规则重放可说明设计意图，但不能证明当前真实 EDA 文档、PCB 状态或保存重载已经通过。", locations=["fixtureMetadata.liveEdaVerified"],
                     evidence=[{"liveEdaVerified": False, "executionStatus": metadata.get("executionStatus")}], calculation="liveEdaVerified=false",
                     recommendationZh="保持当前严格评级为待复验，并在真实 EDA 中完成全部六项门禁。",
                     revalidation="从当前页面重新采集 ERC、DRC、未布通、板框及保存重载证据。", unresolvedAssumptions=[], ruleFamily="evidence_gate")

        completeness["missingFields"] = sorted(set(completeness["missingFields"]))
        completeness["invalidFields"] = sorted(set(completeness["invalidFields"]))
        completeness["allRequiredEvidencePresentAndValid"] = not completeness["missingFields"] and not completeness["invalidFields"]
        completeness["allPrototypeGatesPassed"] = (
            completeness["allRequiredEvidencePresentAndValid"]
            and all(gates[field] in {"pass", "explained"} for field in REQUIRED_PROTOTYPE_GATES)
            and not contradictions
            and not completeness["scopeLimitations"]
        )
        if contradictions:
            completeness["status"] = "conflicting"
        elif completeness["missingFields"] or completeness["invalidFields"] or completeness["scopeLimitations"]:
            completeness["status"] = "incomplete"
        else:
            completeness["status"] = "complete"

    def rule_ground_and_topology(self) -> None:
        ground = self.d.get("groundReview", {})
        if ground:
            pours = int(ground.get("pours", 0))
            islands = int(ground.get("islands", 0))
            return_ok = ground.get("returnPathVerified")
            split_ok = ground.get("powerLogicReturnSeparated")
            if pours == 0 or islands > 0:
                severity = "blocker"
            elif return_ok is False or split_ok is False:
                severity = "advisory"
            else:
                severity = "pass"
            self.add(
                id="GROUND_RETURN", severity=severity, confidence=ground.get("confidence", "medium"),
                title="GND 铜皮、孤岛与高电流回流" + ("需要修正" if severity == "blocker" else ("需要复核" if severity == "advisory" else "通过")),
                riskZh="高 di/dt 负载回流与逻辑地混流会引入复位、通信和传感器干扰。" if severity != "pass" else "铜皮连续性和功率/逻辑回流分区通过配置检查。",
                locations=ground.get("locations", []), evidence=[ground],
                calculation=f"pours={pours}; islands={islands}; returnPathVerified={return_ok}; powerLogicReturnSeparated={split_ok}",
                recommendationZh="消除孤岛和狭颈，使功率回路局部闭合，并把逻辑地与功率回流在定义位置汇聚。",
                revalidation="从铜皮、过孔、功率路径和关键回流截图复核，并在动态负载下测量噪声/复位。",
                unresolvedAssumptions=ground.get("assumptions", []), ruleFamily="ground")
        topology = self.d.get("schematicTopology", {})
        if topology:
            floating = topology.get("floatingInputs", [])
            conflicts = topology.get("sameNameConflicts", [])
            pinpad = topology.get("pinPadVerified")
            hidden = topology.get("hiddenPowerPinsVerified")
            if floating or conflicts or pinpad is False:
                severity = "blocker"
            elif hidden is False:
                severity = "advisory"
            else:
                severity = "pass"
            self.add(
                id="SCHEMATIC_TOPOLOGY", severity=severity, confidence=topology.get("confidence", "high"),
                title="原理图输入、隐藏电源脚、同名网络与 pin-to-pad 一致性" + ("存在问题" if severity != "pass" else "通过"),
                riskZh="悬空输入、错误同名网络、隐藏电源脚遗漏或 pin-to-pad 不一致会造成随机行为或实物功能错误。" if severity != "pass" else "配置的拓扑、隐藏电源和 pin-to-pad 检查通过。",
                locations=list(floating) + list(conflicts), evidence=[topology],
                calculation=f"floatingInputs={len(floating)}; sameNameConflicts={len(conflicts)}; pinPadVerified={pinpad}; hiddenPowerPinsVerified={hidden}",
                recommendationZh="为输入提供确定状态，逐项核验隐藏电源脚、网络别名和 symbol→footprint→pad 映射。",
                revalidation="保存重载后重新运行 ERC、网络等价、隐藏电源和 pin-to-pad 检查。",
                unresolvedAssumptions=topology.get("assumptions", []), ruleFamily="schematic_topology")

    def rule_firmware_pins(self) -> None:
        pins = self.d.get("firmwarePins", [])
        by_pin: dict[str, list[dict[str, Any]]] = {}
        for row in pins:
            by_pin.setdefault(row["pin"], []).append(row)
        for pin, rows in by_pin.items():
            active = [r for r in rows if r.get("net") not in {None, "NC", "GND", "+3V3", "+5V"}]
            if len({r.get("net") for r in active}) > 1:
                self.add(id=f"FIRMWARE_PIN_CONFLICT:{pin}", severity="blocker", confidence="high", title="固件管脚分配冲突", riskZh="一个 MCU 管脚被分配到多个不兼容功能。",
                         locations=[pin], evidence=active, calculation=f"nets={sorted({r.get('net') for r in active})}", recommendationZh="重新分配管脚或确认复用时序互斥。",
                         revalidation="原理图网络与固件 manifest 双向比对。", unresolvedAssumptions=[], ruleFamily="firmware")

    def result(self) -> dict[str, Any]:
        def rating_for(findings: list[Finding]) -> tuple[str, list[str]]:
            blockers = [f for f in findings if f.severity == "blocker" and confidence_rank(f.confidence) >= confidence_rank("high")]
            all_blockers = [f for f in findings if f.severity == "blocker"]
            advisories = [f for f in findings if f.severity == "advisory"]
            unresolved = sorted({x for f in findings if f.severity != "pass" for x in f.unresolvedAssumptions})
            if blockers:
                return RATING_UNSUITABLE, unresolved
            if all_blockers or advisories or unresolved:
                return RATING_FIX_FIRST, unresolved
            return RATING_SUITABLE, unresolved

        rating, unresolved = rating_for(self.findings)
        forecast_findings = [f for f in self.findings if not f.id.startswith(EVIDENCE_ONLY_FINDING_PREFIXES)]
        engineering_forecast_rating, _forecast_unresolved = rating_for(forecast_findings)
        all_blockers = [f for f in self.findings if f.severity == "blocker"]
        advisories = [f for f in self.findings if f.severity == "advisory"]
        return {
            "schema": "jlceda-prototype-review/1.0",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "mode": "Prototype Review",
            "designName": self.d.get("designName", "current JLCEDA design"),
            "rating": rating,
            "engineeringForecastRating": engineering_forecast_rating,
            "evidenceCompleteness": sanitize_public_value(self.evidence_completeness),
            "ratingAlgorithm": {
                "highConfidenceBlocker": RATING_UNSUITABLE,
                "advisoryOrMissingCriticalEvidence": RATING_FIX_FIRST,
                "prototypeGatesComplete": RATING_SUITABLE,
                "drcZeroIsSufficient": False,
                "engineeringForecastExcludesEvidenceGateFindings": True,
            },
            "counts": {
                "pass": sum(f.severity == "pass" for f in self.findings),
                "advisory": len(advisories),
                "blocker": len(all_blockers),
            },
            "unresolvedAssumptions": unresolved,
            "findings": [asdict(f) for f in self.findings],
            "sourceEvidence": sanitize_public_value(self.d.get("sourceEvidence", [])),
        }


def normalize_raw_input(spec: dict[str, Any], spec_path: Path) -> dict[str, Any]:
    if "rawEvidence" not in spec:
        return spec
    base = spec_path.parent
    raw = spec["rawEvidence"]
    schematic = read_json((base / raw["schematic"]).resolve())
    pcb = read_json((base / raw["pcb"]).resolve())
    context = spec["designContext"]
    components = []
    context_components = context.get("components", {})
    for c in pcb.get("components", []):
        extra = context_components.get(c["designator"], {})
        merged = {
            "ref": c["designator"], "value": c.get("value"), "package": c.get("footprint"),
            "x": c.get("x"), "y": c.get("y"), "nets": sorted({p.get("net") for p in c.get("pads", []) if p.get("net")}),
        }
        merged.update(extra)
        components.append(merged)
    nets = []
    net_context = context.get("nets", {})
    for w in pcb.get("wires", []):
        extra = net_context.get(w["net"], {})
        row = {"name": w["net"], "minWidthMm": w.get("width", {}).get("min"), "maxWidthMm": w.get("width", {}).get("max"), "vias": w.get("vias", 0)}
        row.update(extra)
        nets.append(row)
    seen = {n["name"] for n in nets}
    for name, extra in net_context.items():
        if name not in seen:
            row = {"name": name}
            row.update(extra)
            nets.append(row)
    checks = dict(context.get("checks", {}))
    design = {
        "schema": "jlceda-prototype-review-input/1.0",
        "designName": context.get("designName", spec.get("designName", "current JLCEDA design")),
        "components": components,
        "nets": nets,
        "checks": checks,
        "sourceEvidence": [raw["schematic"], raw["pcb"]],
        "observedCounts": {
            "schematicComponents": schematic.get("componentCount"), "schematicPins": schematic.get("pinCount"),
            "schematicConnectedPins": schematic.get("connectedPinCount"), "schematicNets": schematic.get("netCount"),
            "pcbComponents": len(pcb.get("components", [])), "pcbVias": len(pcb.get("vias", [])), "pcbPours": len(pcb.get("polygons", [])),
        },
    }
    if "fixtureMetadata" in context:
        design["fixtureMetadata"] = context["fixtureMetadata"]
    elif "fixtureMetadata" in spec:
        design["fixtureMetadata"] = spec["fixtureMetadata"]
    for key in ["powerPaths", "protectedCircuits", "hbridgeUses", "regulatorUses", "decouplingRequirements", "bulkCapRequirements", "voltageDividers", "debugInterface", "usability", "pcb", "groundReview", "schematicTopology", "firmwarePins"]:
        design[key] = context.get(key, [] if key not in {"debugInterface", "usability", "pcb", "groundReview", "schematicTopology"} else {})
    return design


def render_report(result: dict[str, Any]) -> str:
    findings = result["findings"]
    blockers = [f for f in findings if f["severity"] == "blocker"]
    advisories = [f for f in findings if f["severity"] == "advisory"]
    passes = [f for f in findings if f["severity"] == "pass"]
    lines = [
        f"# {result['designName']} — Prototype 自动审核报告", "", f"**最终评级：{RATING_LABEL_ZH.get(result['rating'], result['rating'])}**", "",
        "> DRC=0 仅是审核输入之一。本评级同时考虑额定值、电源、电流、热、封装、接口、布局和缺失证据。", "",
        f"- 🔴 blocker：{len(blockers)}", f"- 🟡 advisory：{len(advisories)}", f"- 🟢 pass：{len(passes)}", "",
    ]
    for title, icon, group in [("阻止样板", "🔴", blockers), ("修改后建议打样", "🟡", advisories), ("已通过", "🟢", passes)]:
        lines += [f"## {icon} {title}", ""]
        if not group:
            lines += ["无。", ""]
        for f in group:
            lines += [
                f"### {f['id']} — {f['title']}", "", f"- **普通用户风险：** {f['riskZh']}",
                f"- **位置：** {', '.join(f['locations']) or '全局'}", f"- **计算：** `{f['calculation']}`",
                f"- **修改建议：** {f['recommendationZh']}", f"- **复验：** {f['revalidation']}",
                f"- **证据置信度：** {f['confidence']}",
            ]
            if f["unresolvedAssumptions"]:
                lines.append(f"- **待确认：** {'；'.join(f['unresolvedAssumptions'])}")
            lines.append("")
    lines += ["## 结论边界", "", "这是 Prototype 样板前门禁，不替代实物上电、负载、温升、EMC、机械和寿命测试，也不构成 Manufacturing Release。", ""]
    return "\n".join(lines)


def render_summary(result: dict[str, Any]) -> str:
    findings = result["findings"]
    risks = [f for f in findings if f["severity"] in {"blocker", "advisory"}][:3]
    passes = [f for f in findings if f["severity"] == "pass"][:5]
    lines = ["# 用户只需看这一页", "", f"## 最终评级：**{RATING_LABEL_ZH.get(result['rating'], result['rating'])}**", "", "## 前三项风险", ""]
    lines += [f"{i}. **{f['title']}**：{f['riskZh']}" for i, f in enumerate(risks, 1)] or ["当前规则未发现工程风险。"]
    lines += ["", "## 已通过", ""] + ([f"- {f['title']}" for f in passes] or ["- 暂无可确认的通过项。"])
    lines += ["", "## 用户接下来需要做什么", ""]
    if result["rating"] == RATING_UNSUITABLE:
        lines.append("先处理报告中的 blocker，再重新运行自动审核和有限首板实验门。")
    elif result["rating"] == RATING_FIX_FIRST:
        lines.append("补齐关键参数并处理 advisory，然后重新审核；当前结论不直接升级为 Prototype 放行。")
    else:
        lines.append("可进入 2–5 块低风险样板的人工确认与受控首板测试。")
    lines += ["", "审核模式：Prototype Review；不是 Manufacturing Release。", ""]
    return "\n".join(lines)


def write_firmware(path: Path, pins: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["pin", "port", "net", "purpose", "direction"])
        writer.writeheader()
        for p in pins:
            writer.writerow({k: p.get(k, "") for k in writer.fieldnames})


def emit_outputs(design: dict[str, Any], result: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    machine = output / "machine-review.json"
    report = output / "prototype-review-report-zh.md"
    summary = output / "one-page-summary-zh.md"
    firmware = output / "firmware-pin-map.csv"
    screenshot_index = output / "screenshot-index.json"
    write_json(machine, result)
    report.write_text(render_report(result), encoding="utf-8")
    summary.write_text(render_summary(result), encoding="utf-8")
    write_firmware(firmware, design.get("firmwarePins", []))
    write_json(screenshot_index, {"screenshots": sanitize_public_value(design.get("screenshots", [])), "note": "截图索引来自只读采集；引擎不执行 EDA 写入。"})
    files = []
    for p in [machine, report, summary, firmware, screenshot_index]:
        files.append({"path": p.name, "sha256": sha256(p), "bytes": p.stat().st_size})
    write_json(output / "evidence-manifest.json", {
        "schema": "jlceda-prototype-review-manifest/1.0", "generatedAt": datetime.now(timezone.utc).isoformat(),
        "rating": result["rating"], "files": files, "sourceEvidence": result.get("sourceEvidence", []), "edaWrites": 0,
    })


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="JLCEDA Prototype read-only engineering review")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--profiles", type=Path, default=Path(__file__).with_name("component-profiles.json"))
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--normalized-output", type=Path)
    args = ap.parse_args(argv)
    try:
        spec = read_json(args.input)
        design = validate_design(normalize_raw_input(spec, args.input.resolve()))
        profiles = validate_profiles(read_json(args.profiles))
        if args.normalized_output:
            write_json(args.normalized_output, sanitize_public_value(design))
        result = Review(design, profiles).run()
        emit_outputs(design, result, args.output)
    except (OSError, json.JSONDecodeError, InputValidationError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": sanitize_public_value(str(exc))}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"rating": result["rating"], "counts": result["counts"], "output": sanitize_public_value(str(args.output))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
