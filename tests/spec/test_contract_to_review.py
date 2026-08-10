import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SPEC_DIR = REPO / "src" / "spec"
REVIEW_DIR = REPO / "src" / "review"
SCRIPT = REPO / "scripts" / "contract-to-review-cli.py"
PROFILES_PATH = REVIEW_DIR / "component-profiles.json"
sys.path.insert(0, str(SPEC_DIR))
sys.path.insert(0, str(REVIEW_DIR))

from contract_to_review import (  # noqa: E402
    ContractInputError,
    contract_to_review_input,
    contract_to_review_issues,
)
from prototype_review import (  # noqa: E402
    RATING_FIX_FIRST,
    RATING_SUITABLE,
    RATING_UNSUITABLE,
    Review,
    validate_design,
)


def base_contract(**overrides):
    """A structurally complete M2-like hardware contract (all schema keys present)."""
    contract = {
        "schemaVersion": "1.0.0",
        "kind": "hardware-contract",
        "status": "requirements-complete",
        "generatedAt": "2026-08-09T00:00:00+00:00",
        "sourceSnapshot": "sha256:" + "0" * 64,
        "board": {
            "projectUuid": "00000000-0000-0000-0000-000000000000",
            "projectName": "M2 电源分配板测试",
            "boardName": "M2 电源分配板测试",
            "schematicUuid": None,
            "pcbUuid": None,
        },
        "components": [
            {"designator": "J1", "name": "输入连接器 J1", "manufacturerId": None, "supplierId": None, "footprintUuid": None, "approved": False},
            {"designator": "J2", "name": "输出连接器 J2", "manufacturerId": None, "supplierId": None, "footprintUuid": None, "approved": False},
            {"designator": "J3", "name": "输出连接器 J3", "manufacturerId": None, "supplierId": None, "footprintUuid": None, "approved": False},
        ],
        "signals": [],
        "interfaces": [],
        "powerDomains": [
            {"name": "+5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 1.0, "approved": False},
            {"name": "GND", "nominalVoltageV": 0.0, "minVoltageV": 0.0, "maxVoltageV": 0.0, "maxCurrentA": 1.0, "approved": False},
        ],
        "constraints": [
            {
                "kind": "mechanical",
                "boardSizeMm": {"widthMm": 60, "heightMm": 40},
                "connectorPositions": [
                    {"name": "J1", "positionMm": "(-18.8, 0)"},
                    {"name": "J2", "positionMm": "(18.8, 5)"},
                    {"name": "J3", "positionMm": "(18.8, -5)"},
                ],
                "notes": None,
                "approved": False,
            }
        ],
        "approvals": {"componentSelection": False, "pinMap": False, "electricalRules": False, "firmwareBinding": False},
        "unresolved": [],
    }
    contract.update(overrides)
    return contract


def m2_like_contract():
    return base_contract()


def capacitor_contract():
    """One power capacitor with coordinates, one +5V/GND power pair."""
    return base_contract(
        components=[
            {"designator": "C1", "name": "10uF", "manufacturerId": "CL21B104KBCNNNC", "supplierId": None, "footprintUuid": None, "approved": False},
        ],
        powerDomains=[
            {"name": "+5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 1.0, "approved": False},
            {"name": "GND", "nominalVoltageV": 0.0, "minVoltageV": 0.0, "maxVoltageV": 0.0, "maxCurrentA": 1.0, "approved": False},
        ],
        constraints=[
            {
                "kind": "mechanical",
                "boardSizeMm": {"widthMm": 60, "heightMm": 40},
                "connectorPositions": [{"name": "C1", "positionMm": "(12, -3)"}],
                "notes": None,
                "approved": False,
            }
        ],
    )


class ContractToReviewTests(unittest.TestCase):
    def convert(self, contract, **kwargs):
        return contract_to_review_input(copy.deepcopy(contract), **kwargs)

    def issues(self, contract, **kwargs):
        return contract_to_review_issues(copy.deepcopy(contract), **kwargs)

    # ---- 1. complete contract maps every field ----
    def test_complete_contract_produces_reviewable_input(self):
        review = self.convert(m2_like_contract())
        self.assertEqual(review["schema"], "jlceda-prototype-review-input/1.0")
        self.assertIs(validate_design(review), review)
        net_names = [net["name"] for net in review["nets"]]
        self.assertEqual(net_names, ["+5V", "GND"])
        plus5v = review["nets"][0]
        self.assertEqual(plus5v["role"], "power")
        self.assertEqual(plus5v["designCurrentA"], 1.0)
        gnd = review["nets"][1]
        self.assertEqual(gnd["role"], "high_current_return")
        self.assertEqual(gnd["designCurrentA"], 1.0)
        by_ref = {c["ref"]: c for c in review["components"]}
        self.assertEqual(list(by_ref), ["J1", "J2", "J3"])
        self.assertEqual(by_ref["J1"]["x"], -18.8)
        self.assertEqual(by_ref["J1"]["y"], 0.0)
        self.assertEqual(by_ref["J2"]["x"], 18.8)
        self.assertEqual(by_ref["J2"]["y"], 5.0)
        self.assertEqual(by_ref["J1"]["nets"], ["+5V", "GND"])
        self.assertEqual(by_ref["J2"]["nets"], ["+5V", "GND"])
        self.assertNotIn("mpn", by_ref["J1"])
        self.assertNotIn("package", by_ref["J1"])
        self.assertNotIn("critical", by_ref["J1"])
        self.assertNotIn("profile", by_ref["J1"])
        self.assertEqual(review["checks"]["requirementsComplete"], True)
        self.assertEqual(review["checks"]["savedReloaded"], False)
        self.assertEqual(review["fixtureMetadata"]["liveEdaVerified"], False)
        self.assertEqual(review["fixtureMetadata"]["notForManufacturing"], True)
        self.assertEqual(review["sourceEvidence"], ["requirements gate hardware-contract (offline, synthesized)"])
        # a fully positioned M2-like contract is mapped without loss
        self.assertEqual(self.issues(m2_like_contract()), [])

    # ---- 2. missing mechanical -> no coordinates, issues register them ----
    def test_missing_mechanical_omits_coordinates_and_logs_them(self):
        contract = m2_like_contract()
        contract["constraints"] = []
        review = self.convert(contract)
        self.assertIs(validate_design(review), review)
        for component in review["components"]:
            self.assertNotIn("x", component)
            self.assertNotIn("y", component)
            self.assertNotIn("nets", component)
        issues = self.issues(contract)
        text = "\n".join(issues)
        self.assertIn("component:J1:缺少可用的机械坐标(connectorPositions),已省略", text)
        self.assertIn("component:J1:缺少器件级网络连接信息(nets),已省略", text)

    # ---- 3. no device-level nets -> nets omitted and logged ----
    def test_component_without_position_match_omits_nets_and_logs_them(self):
        contract = base_contract(
            components=[
                {"designator": "J1", "name": "输入连接器 J1", "manufacturerId": None, "supplierId": None, "footprintUuid": None, "approved": False},
                {"designator": "U1", "name": "主控", "manufacturerId": "STM32F103C8T6", "supplierId": "LCSC:C9652", "footprintUuid": None, "approved": False},
            ],
            constraints=[
                {
                    "kind": "mechanical",
                    "boardSizeMm": {"widthMm": 60, "heightMm": 40},
                    "connectorPositions": [{"name": "J1", "positionMm": "(-18.8, 0)"}],
                    "notes": None,
                    "approved": False,
                }
            ],
        )
        review = self.convert(contract)
        by_ref = {c["ref"]: c for c in review["components"]}
        self.assertEqual(by_ref["J1"]["nets"], ["+5V", "GND"])
        self.assertNotIn("nets", by_ref["U1"])
        issues = self.issues(contract)
        self.assertIn("component:U1:缺少器件级网络连接信息(nets),已省略", issues)
        self.assertIn("component:U1:缺少可用的机械坐标(connectorPositions),已省略", issues)
        self.assertNotIn("component:J1", "\n".join(issues))

    # ---- 4. empty components -> hard error ----
    def test_empty_components_are_rejected(self):
        contract = m2_like_contract()
        contract["components"] = []
        with self.assertRaises(ContractInputError):
            self.convert(contract)
        with self.assertRaises(ContractInputError):
            self.issues(contract)

    # ---- 5. malformed contracts -> ContractInputError ----
    def test_non_contract_inputs_are_rejected(self):
        with self.assertRaises(ContractInputError):
            self.convert(["not", "a", "contract"])
        with self.assertRaises(ContractInputError):
            self.convert(None)

    def test_missing_required_keys_are_rejected(self):
        contract = m2_like_contract()
        del contract["powerDomains"]
        with self.assertRaises(ContractInputError):
            self.convert(contract)
        contract = m2_like_contract()
        del contract["components"]
        with self.assertRaises(ContractInputError):
            self.convert(contract)

    def test_wrong_kind_is_rejected(self):
        contract = m2_like_contract()
        contract["kind"] = "some-other-document"
        with self.assertRaises(ContractInputError):
            self.convert(contract)

    def test_wrong_field_types_are_rejected(self):
        contract = m2_like_contract()
        contract["components"][0]["designator"] = 7
        with self.assertRaises(ContractInputError):
            self.convert(contract)
        contract = m2_like_contract()
        contract["components"] = ["J1"]
        with self.assertRaises(ContractInputError):
            self.convert(contract)
        contract = m2_like_contract()
        contract["powerDomains"] = "5V"
        with self.assertRaises(ContractInputError):
            self.convert(contract)
        contract = m2_like_contract()
        contract["powerDomains"][0]["nominalVoltageV"] = "5V"
        with self.assertRaises(ContractInputError):
            self.convert(contract)

    def test_duplicate_power_domain_names_are_rejected(self):
        contract = m2_like_contract()
        contract["powerDomains"].append({"name": "+5V", "nominalVoltageV": 5.0, "maxCurrentA": 2.0, "approved": False})
        with self.assertRaises(ContractInputError):
            self.convert(contract)

    def test_duplicate_component_designators_are_rejected(self):
        contract = m2_like_contract()
        contract["components"][1]["designator"] = "J1"
        with self.assertRaises(ContractInputError):
            self.convert(contract)

    def test_conflicting_duplicate_positions_are_rejected(self):
        contract = m2_like_contract()
        contract["constraints"][0]["connectorPositions"].append({"name": "J1", "positionMm": "(1, 1)"})
        with self.assertRaises(ContractInputError):
            self.convert(contract)

    def test_identical_duplicate_positions_are_deduplicated_silently(self):
        # Quality review Minor #3: identical duplicate positions should dedupe
        # to one entry without raising (only conflicting duplicates reject).
        contract = m2_like_contract()
        original = contract["constraints"][0]["connectorPositions"][0]
        contract["constraints"][0]["connectorPositions"].append(dict(original))
        review = self.convert(contract)  # must not raise
        j1 = next(c for c in review["components"] if c["ref"] == "J1")
        self.assertIn("x", j1)
        self.assertIn("y", j1)

    # ---- 6. determinism and no timestamps ----
    def test_deterministic_output_bytes(self):
        first = self.convert(m2_like_contract())
        second = self.convert(m2_like_contract())
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, indent=2, sort_keys=True),
            json.dumps(second, ensure_ascii=False, indent=2, sort_keys=True),
        )
        self.assertEqual(self.issues(m2_like_contract()), self.issues(m2_like_contract()))

    def test_no_timestamps_and_now_never_affects_output(self):
        review = self.convert(m2_like_contract(), now="2026-08-09T00:00:00+00:00")
        serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("generatedAt", serialized)
        self.assertNotIn("2026", serialized)
        with_now = json.dumps(self.convert(m2_like_contract(), now="2026-08-09T00:00:00+00:00"), ensure_ascii=False, sort_keys=True)
        without_now = json.dumps(self.convert(m2_like_contract()), ensure_ascii=False, sort_keys=True)
        self.assertEqual(with_now, without_now)

    def test_invalid_now_and_options_are_rejected(self):
        with self.assertRaises(ContractInputError):
            self.convert(m2_like_contract(), now="not-a-timestamp")
        with self.assertRaises(ContractInputError):
            self.convert(m2_like_contract(), options=["not", "a", "mapping"])

    # ---- 7. converted output actually runs the review engine ----
    def test_converted_input_runs_review_engine_end_to_end(self):
        profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        review = self.convert(capacitor_contract())
        self.assertIs(validate_design(review), review)
        c1 = review["components"][0]
        self.assertEqual(c1["ref"], "C1")
        self.assertEqual(c1["mpn"], "CL21B104KBCNNNC")
        self.assertEqual(c1["value"], "10uF")
        self.assertEqual(c1["capacitanceUf"], 10.0)
        self.assertEqual(c1["x"], 12.0)
        self.assertEqual(c1["y"], -3.0)
        self.assertEqual(c1["nets"], ["+5V", "GND"])
        result = Review(review, profiles).run()
        self.assertIn(result["rating"], (RATING_UNSUITABLE, RATING_FIX_FIRST, RATING_SUITABLE))
        self.assertIsInstance(result["findings"], list)

    # ---- 8. zero third-party dependencies and Python 3.10 compatibility ----
    def test_no_third_party_imports(self):
        for path in (SPEC_DIR / "contract_to_review.py", SCRIPT):
            source = path.read_text(encoding="utf-8")
            for banned in ("jsonschema", "import yaml", "requests", "numpy", "pandas"):
                self.assertNotIn(banned, source)
        for banned in ("jsonschema", "yaml", "requests", "numpy", "pandas"):
            self.assertNotIn(banned, sys.modules)

    def test_python_310_compatible_annotations(self):
        source = (SPEC_DIR / "contract_to_review.py").read_text(encoding="utf-8")
        self.assertIn("from __future__ import annotations", source)
        self.assertIn("str | None", source)

    # ---- extra: value derivation heuristic ----
    def test_value_derivation_only_for_value_like_names(self):
        review = self.convert(capacitor_contract())
        self.assertEqual(review["components"][0]["value"], "10uF")
        review = self.convert(m2_like_contract())
        for component in review["components"]:
            self.assertNotIn("value", component)  # "输入连接器 J1" etc. are not values

    # ---- extra: capacitance parsing ----
    def test_capacitance_parsing_units(self):
        self.assertEqual(contract_to_review_input(
            base_contract(
                components=[
                    {"designator": "C1", "name": "100nF", "manufacturerId": None, "supplierId": None, "footprintUuid": None, "approved": False},
                ]
            )
        )["components"][0]["capacitanceUf"], 0.1)
        review = contract_to_review_input(
            base_contract(
                components=[
                    {"designator": "C2", "name": "1F", "manufacturerId": None, "supplierId": None, "footprintUuid": None, "approved": False},
                ]
            )
        )
        self.assertEqual(review["components"][0]["capacitanceUf"], 1000000.0)
        # non-capacitor names are not parsed
        review = contract_to_review_input(m2_like_contract())
        for component in review["components"]:
            self.assertNotIn("capacitanceUf", component)

    # extra: capacitance regex must not false-positive on names that merely
    # contain a capacitance-looking substring (quality review Minor #1).
    def test_capacitance_regex_rejects_false_positives(self):
        for name in ("C10uF block", "10uF capacitor", "10uF-MLCC", "10mF", "10u"):
            review = contract_to_review_input(
                base_contract(
                    components=[
                        {"designator": "C1", "name": name, "manufacturerId": None, "supplierId": None, "footprintUuid": None, "approved": False},
                    ]
                )
            )
            self.assertNotIn(
                "capacitanceUf",
                review["components"][0],
                f"name {name!r} should not parse as a capacitance value",
            )

    # ---- extra: unnamed power domain is skipped and logged ----
    def test_unnamed_power_domain_is_skipped_and_logged(self):
        contract = m2_like_contract()
        contract["powerDomains"][0]["name"] = None
        issues = self.issues(contract)
        self.assertTrue(any("powerDomain:#1:缺少域名" in entry for entry in issues))
        review = self.convert(contract)
        self.assertEqual([net["name"] for net in review["nets"]], ["GND"])
        self.assertEqual(review["components"][0]["nets"], ["GND"])

    # ---- extra: missing maxCurrentA is logged and omitted ----
    def test_missing_domain_current_is_logged_and_omitted(self):
        contract = m2_like_contract()
        contract["powerDomains"][0]["maxCurrentA"] = None
        review = self.convert(contract)
        plus5v = review["nets"][0]
        self.assertNotIn("designCurrentA", plus5v)
        issues = self.issues(contract)
        self.assertIn("powerDomain:+5V:缺少最大电流(maxCurrentA),designCurrentA已省略", issues)

    # ---- extra: unparseable positions and unmatched positions are logged ----
    def test_unparseable_and_unmatched_positions_are_logged(self):
        contract = m2_like_contract()
        contract["constraints"][0]["connectorPositions"].append({"name": "X1", "positionMm": "not-a-position"})
        contract["constraints"][0]["connectorPositions"].append({"name": "C9", "positionMm": "(1, 1)"})
        issues = self.issues(contract)
        self.assertIn("mechanical:connectorPositions:X1:坐标无法解析(positionMm='not-a-position'),已忽略", issues)
        self.assertIn("mechanical:connectorPositions:C9:未匹配到组件(designator),已忽略", issues)

    # ---- extra: designName fallback ----
    def test_missing_design_name_uses_placeholder_and_is_logged(self):
        contract = m2_like_contract()
        contract["board"]["projectName"] = None
        contract["board"]["boardName"] = None
        review = self.convert(contract)
        self.assertTrue(review["designName"])
        issues = self.issues(contract)
        self.assertTrue(any(entry.startswith("design:缺少设计名称") for entry in issues))

    # ---- extra: null designator entries are skipped and logged ----
    def test_null_designator_component_is_skipped_and_logged(self):
        contract = m2_like_contract()
        contract["components"].append(
            {"designator": None, "name": "未贴装器件", "manufacturerId": None, "supplierId": None, "footprintUuid": None, "approved": False}
        )
        review = self.convert(contract)
        self.assertEqual([c["ref"] for c in review["components"]], ["J1", "J2", "J3"])
        issues = self.issues(contract)
        self.assertIn("component:未贴装器件:缺少设计位号(designator),已省略该条目", issues)

    # ---- extra: incomplete contract status flows into requirementsComplete ----
    def test_incomplete_contract_status_mirrored(self):
        contract = m2_like_contract()
        contract["status"] = "requirements-incomplete"
        contract["unresolved"] = ["component:m1:缺少制造商ID(manufacturerId)"]
        review = self.convert(contract)
        self.assertEqual(review["checks"]["requirementsComplete"], False)

    # ---- extra: CLI ----
    def test_cli_writes_output_and_issues_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path = root / "contract.json"
            output_path = root / "review-input.json"
            issues_path = root / "issues.txt"
            contract_path.write_text(json.dumps(m2_like_contract()), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--contract", str(contract_path), "--output", str(output_path), "--issues-output", str(issues_path)],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            review = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(review["schema"], "jlceda-prototype-review-input/1.0")
            self.assertEqual(issues_path.read_text(encoding="utf-8"), "")

            no_mech = root / "no-mech.json"
            bad_output = root / "rejected.json"
            no_mech.write_text(json.dumps({**m2_like_contract(), "constraints": []}), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--contract", str(no_mech), "--output", str(bad_output), "--issues-output", str(issues_path)],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue("缺少可用的机械坐标" in issues_path.read_text(encoding="utf-8"))

            bad_contract = root / "bad.json"
            rejected_output = root / "never-written.json"
            bad_contract.write_text(json.dumps({"kind": "hardware-contract", "components": []}), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--contract", str(bad_contract), "--output", str(rejected_output)],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertFalse(rejected_output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
