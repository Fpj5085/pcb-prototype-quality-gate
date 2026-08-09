import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SPEC_DIR = REPO / "src" / "spec"
SCHEMA_DIR = REPO / "schemas"
SCRIPT = REPO / "scripts" / "requirements-gate.py"
sys.path.insert(0, str(SPEC_DIR))

from requirements_gate import (  # noqa: E402
    ContractViolationError,
    RequirementsInputError,
    gate_requirements_to_contract,
    read_json,
    validate_requirements_input,
)

FIXED_NOW = "2026-08-09T00:00:00+00:00"


def complete_input() -> dict:
    """A fully specified requirements input that must gate as complete."""
    return {
        "schemaVersion": "1.0.0",
        "kind": "jlceda-requirements-input/1.0",
        "description": "一辆基于 STM32 的小车控制板",
        "powerInput": {
            "maxCurrentA": 1.0,
            "voltageDomains": [
                {"name": "5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 1.0},
                {"name": "3V3", "nominalVoltageV": 3.3, "minVoltageV": 3.0, "maxVoltageV": 3.6, "maxCurrentA": 0.3},
            ],
        },
        "functionModules": [
            {
                "id": "mcu",
                "name": "主控",
                "role": "主控与电机逻辑",
                "designator": "U1",
                "voltageDomain": "3V3",
                "requiredSignals": 8,
                "maxCurrentA": 0.1,
                "ratedCurrentA": 0.15,
                "manufacturerId": "STM32F103C8T6",
                "supplierId": "LCSC:C9652",
                "footprintUuid": "fp-mcu-0001",
            },
            {
                "id": "driver",
                "name": "电机驱动",
                "role": "双路电机 H 桥驱动",
                "designator": "U2",
                "voltageDomain": "5V",
                "requiredSignals": 6,
                "maxCurrentA": 0.6,
                "ratedCurrentA": 0.8,
                "manufacturerId": "L9110S",
                "supplierId": "LCSC:C51118",
            },
        ],
        "interfaceRequirements": [
            {
                "name": "串口",
                "direction": "bidirectional",
                "voltageDomain": "3V3",
                "signals": [
                    {"name": "UART_TX", "mcuPin": "PA9", "direction": "output", "activeLevel": "high", "voltageDomain": "3V3"},
                    {"name": "UART_RX", "mcuPin": "PA10", "direction": "input", "activeLevel": "high", "voltageDomain": "3V3"},
                ],
            }
        ],
        "mechanical": {"boardSizeMm": {"widthMm": 60, "heightMm": 40}},
        "acceptanceCriteria": ["固件可烧录并能驱动两个电机转动", "串口命令可控制速度与转向"],
        "providedMaterials": [
            {"forModule": "driver", "footprintUuid": "fp-driver-0001"},
        ],
    }


class RequirementsGateTests(unittest.TestCase):
    def gate(self, requirements, now=FIXED_NOW):
        return gate_requirements_to_contract(copy.deepcopy(requirements), now=now)

    def test_complete_input_produces_complete_contract(self):
        contract = self.gate(complete_input())
        self.assertEqual(contract["kind"], "hardware-contract")
        self.assertEqual(contract["status"], "requirements-complete")
        self.assertEqual(contract["unresolved"], [])
        self.assertTrue(contract["sourceSnapshot"].startswith("sha256:"))
        self.assertTrue(len(contract["board"]["projectUuid"]) >= 1)
        self.assertEqual(len(contract["components"]), 2)
        self.assertEqual(len(contract["signals"]), 2)
        self.assertEqual(len(contract["powerDomains"]), 2)

    def test_contract_surface_matches_hardware_contract_shape(self):
        contract = self.gate(complete_input())
        for key in (
            "schemaVersion", "kind", "status", "generatedAt", "sourceSnapshot", "board",
            "components", "signals", "interfaces", "powerDomains", "constraints",
            "approvals", "unresolved",
        ):
            self.assertIn(key, contract)
        self.assertEqual(set(contract["board"]), {"projectUuid", "projectName", "boardName", "schematicUuid", "pcbUuid"})
        self.assertEqual(set(contract["approvals"]), {"componentSelection", "pinMap", "electricalRules", "firmwareBinding"})
        for component in contract["components"]:
            self.assertEqual(set(component), {"designator", "name", "manufacturerId", "supplierId", "footprintUuid", "approved"})
        for signal in contract["signals"]:
            self.assertEqual(set(signal), {"name", "mcuPin", "direction", "activeLevel", "voltageDomain", "approved"})

    def test_all_gate_outputs_require_human_confirmation(self):
        contract = self.gate(complete_input())
        self.assertTrue(all(component["approved"] is False for component in contract["components"]))
        self.assertTrue(all(signal["approved"] is False for signal in contract["signals"]))
        self.assertTrue(all(domain["approved"] is False for domain in contract["powerDomains"]))
        self.assertTrue(all(flag is False for flag in contract["approvals"].values()))
        self.assertTrue(all(entry["approved"] is False for entry in contract["constraints"]))

    def test_missing_part_evidence_yields_unresolved_and_incomplete(self):
        requirements = {
            "schemaVersion": "1.0.0",
            "kind": "jlceda-requirements-input/1.0",
            "description": "简单控制板",
            "powerInput": {
                "domainName": "5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 1.0,
            },
            "functionModules": [
                {
                    "id": "m1", "name": "主控", "role": "主控", "voltageDomain": "5V",
                    "requiredSignals": 4, "maxCurrentA": 0.1, "ratedCurrentA": 0.2,
                }
            ],
            "interfaceRequirements": [
                {"name": "调试", "direction": "bidirectional", "voltageDomain": "5V", "signals": [{"name": "DBG_SWDIO"}]},
            ],
            "acceptanceCriteria": ["能烧录固件"],
        }
        contract = self.gate(requirements)
        self.assertEqual(contract["status"], "requirements-incomplete")
        self.assertEqual(len(contract["components"]), 1)
        component = contract["components"][0]
        self.assertIsNone(component["manufacturerId"])
        self.assertIsNone(component["supplierId"])
        self.assertIsNone(component["footprintUuid"])
        text = "\n".join(contract["unresolved"])
        self.assertIn("component:m1:缺少制造商ID(manufacturerId)", text)
        self.assertIn("component:m1:缺少供应商ID(supplierId)", text)
        self.assertIn("component:m1:缺少封装证据(footprintUuid)", text)
        self.assertIn("signal:DBG_SWDIO:缺少MCU管脚(mcuPin)", text)

    def test_material_linkage_resolves_missing_footprint_evidence(self):
        contract = self.gate(complete_input())
        driver = next(c for c in contract["components"] if c["name"] == "电机驱动")
        self.assertEqual(driver["footprintUuid"], "fp-driver-0001")
        text = "\n".join(contract["unresolved"])
        self.assertNotIn("footprintUuid", text)

    def test_current_requirement_exceeding_module_rating_rejected(self):
        requirements = complete_input()
        requirements["functionModules"][1]["maxCurrentA"] = 0.9
        requirements["functionModules"][1]["ratedCurrentA"] = 0.8
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_module_missing_max_current_registers_unresolved(self):
        requirements = complete_input()
        del requirements["functionModules"][1]["maxCurrentA"]
        contract = self.gate(requirements)
        self.assertEqual(contract["status"], "requirements-incomplete")
        text = "\n".join(contract["unresolved"])
        self.assertIn("module:driver:缺少额定电流maxCurrentA", text)

    def test_module_and_referenced_domain_missing_current_both_registered(self):
        requirements = complete_input()
        # driver lacks maxCurrentA and its referenced domain 5V lacks maxCurrentA.
        del requirements["functionModules"][1]["maxCurrentA"]
        requirements["powerInput"]["voltageDomains"][0]["maxCurrentA"] = None
        contract = self.gate(requirements)
        self.assertEqual(contract["status"], "requirements-incomplete")
        text = "\n".join(contract["unresolved"])
        self.assertIn("module:driver:缺少额定电流maxCurrentA", text)
        self.assertIn("powerDomain:5V:缺少最大电流(maxCurrentA)", text)

    def test_module_current_exceeding_its_voltage_domain_capacity_rejected(self):
        requirements = complete_input()
        # driver draws from 5V whose domain maxCurrentA is 1.0.
        requirements["functionModules"][1]["maxCurrentA"] = 1.5
        requirements["functionModules"][1]["ratedCurrentA"] = 2.0
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_voltage_domain_without_current_budget_flagged_when_used(self):
        requirements = complete_input()
        requirements["powerInput"]["voltageDomains"][0]["maxCurrentA"] = None  # 5V is used by driver
        contract = self.gate(requirements)
        self.assertEqual(contract["status"], "requirements-incomplete")
        text = "\n".join(contract["unresolved"])
        self.assertIn("powerDomain:5V:缺少最大电流(maxCurrentA)", text)

    def test_duplicate_voltage_domain_with_conflicting_current_rejected(self):
        requirements = complete_input()
        requirements["powerInput"]["voltageDomains"] = [
            {"name": "5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 1.0},
            {"name": "5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 2.0},
            {"name": "3V3", "nominalVoltageV": 3.3, "minVoltageV": 3.0, "maxVoltageV": 3.6, "maxCurrentA": 0.3},
        ]
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_exact_duplicate_voltage_domains_are_deduplicated(self):
        requirements = complete_input()
        requirements["powerInput"]["voltageDomains"] = [
            {"name": "5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 1.0},
            {"name": "5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 1.0},
            {"name": "3V3", "nominalVoltageV": 3.3, "minVoltageV": 3.0, "maxVoltageV": 3.6, "maxCurrentA": 0.3},
        ]
        contract = self.gate(requirements)
        self.assertEqual(len(contract["powerDomains"]), 2)
        self.assertEqual(contract["powerDomains"][0]["name"], "5V")
        self.assertEqual(contract["status"], "requirements-complete")

    def test_material_for_module_by_display_name_links(self):
        requirements = complete_input()
        requirements["providedMaterials"][0]["forModule"] = "电机驱动"  # driver's display name, not its id
        contract = self.gate(requirements)
        driver = next(c for c in contract["components"] if c["name"] == "电机驱动")
        self.assertEqual(driver["footprintUuid"], "fp-driver-0001")
        self.assertNotIn("component:driver:缺少封装证据(footprintUuid)", contract["unresolved"])

    def test_hardware_contract_schema_status_enum_includes_gate_statuses(self):
        schema = json.loads((SCHEMA_DIR / "hardware-contract.schema.json").read_text(encoding="utf-8"))
        enum = schema["properties"]["status"]["enum"]
        self.assertEqual(
            enum,
            ["draft", "reviewed", "approved", "requirements-complete", "requirements-incomplete"],
        )

    def test_total_current_exceeding_power_capacity_rejected(self):
        requirements = complete_input()
        requirements["functionModules"][0]["maxCurrentA"] = 0.7
        requirements["functionModules"][0]["ratedCurrentA"] = 0.9
        requirements["functionModules"][1]["maxCurrentA"] = 0.5
        requirements["functionModules"][1]["ratedCurrentA"] = 0.9
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_inverted_voltage_range_rejected(self):
        requirements = complete_input()
        requirements["powerInput"] = {"domainName": "5V", "nominalVoltageV": 5.0, "minVoltageV": 6.0, "maxVoltageV": 5.0, "maxCurrentA": 1.0}
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_nominal_voltage_outside_range_rejected(self):
        requirements = complete_input()
        requirements["powerInput"] = {"domainName": "5V", "nominalVoltageV": 4.0, "minVoltageV": 4.5, "maxVoltageV": 5.5, "maxCurrentA": 1.0}
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_duplicate_voltage_domain_with_conflicting_definition_rejected(self):
        requirements = complete_input()
        requirements["powerInput"]["voltageDomains"] = [
            {"name": "5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5},
            {"name": "5V", "nominalVoltageV": 5.5, "minVoltageV": 4.5, "maxVoltageV": 5.5},
        ]
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_module_referencing_undeclared_voltage_domain_rejected(self):
        requirements = complete_input()
        requirements["powerInput"]["voltageDomains"] = [
            {"name": "5V", "nominalVoltageV": 5.0, "minVoltageV": 4.5, "maxVoltageV": 5.5},
        ]
        # "mcu" requires 3V3 which is no longer declared.
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_interface_referencing_undeclared_voltage_domain_rejected(self):
        requirements = complete_input()
        requirements["interfaceRequirements"][0]["voltageDomain"] = "12V"
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_material_and_module_disagreeing_on_evidence_rejected(self):
        requirements = complete_input()
        requirements["functionModules"][1]["footprintUuid"] = "fp-a"
        requirements["providedMaterials"][0]["footprintUuid"] = "fp-b"
        with self.assertRaises(ContractViolationError):
            self.gate(requirements)

    def test_schema_violations_are_rejected(self):
        bad_kind = complete_input()
        bad_kind["kind"] = "jlceda-requirements-input/0.9"
        with self.assertRaises(RequirementsInputError):
            self.gate(bad_kind)

        extra_field = complete_input()
        extra_field["unknownTopLevel"] = True
        with self.assertRaises(RequirementsInputError):
            self.gate(extra_field)

        bad_power_type = complete_input()
        bad_power_type["powerInput"] = "5V"
        with self.assertRaises(RequirementsInputError):
            self.gate(bad_power_type)

        bad_module_field = complete_input()
        bad_module_field["functionModules"][0]["unexpected"] = 1
        with self.assertRaises(RequirementsInputError):
            self.gate(bad_module_field)

        bool_as_number = complete_input()
        bool_as_number["powerInput"]["maxCurrentA"] = True
        with self.assertRaises(RequirementsInputError):
            self.gate(bool_as_number)

        non_finite = complete_input()
        non_finite["powerInput"]["maxCurrentA"] = float("inf")
        with self.assertRaises(RequirementsInputError):
            self.gate(non_finite)

    def test_gate_validates_input_internally(self):
        with self.assertRaises(RequirementsInputError):
            gate_requirements_to_contract({"schemaVersion": "1.0.0", "kind": "jlceda-requirements-input/1.0", "powerInput": []})

    def test_read_json_rejects_nonstandard_numeric_constants(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "requirements.json"
            path.write_text('{"a": NaN}', encoding="utf-8")
            with self.assertRaises(RequirementsInputError):
                read_json(path)

    def test_invalid_now_is_rejected(self):
        with self.assertRaises(RequirementsInputError):
            self.gate(complete_input(), now="not-a-timestamp")

    def test_deterministic_output_with_fixed_now(self):
        first = self.gate(complete_input())
        second = self.gate(complete_input())
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, indent=2, sort_keys=True),
            json.dumps(second, ensure_ascii=False, indent=2, sort_keys=True),
        )
        later = self.gate(complete_input(), now="2026-08-09T01:00:00+00:00")
        self.assertNotEqual(first["generatedAt"], later["generatedAt"])
        self.assertEqual(first["unresolved"], later["unresolved"])

    def test_absent_interfaces_flagged_but_explicit_empty_accepted(self):
        absent = complete_input()
        del absent["interfaceRequirements"]
        contract = self.gate(absent)
        self.assertIn("requirements-incomplete", contract["status"])
        self.assertTrue(any("接口需求" in entry for entry in contract["unresolved"]))

        explicit_empty = complete_input()
        explicit_empty["interfaceRequirements"] = []
        contract = self.gate(explicit_empty)
        self.assertEqual(contract["status"], "requirements-complete")
        self.assertFalse(any("接口需求" in entry for entry in contract["unresolved"]))

    def test_mechanical_is_optional_and_never_flagged(self):
        without = complete_input()
        del without["mechanical"]
        contract = self.gate(without)
        self.assertEqual(contract["status"], "requirements-complete")
        self.assertFalse(any("机械" in entry or "mechanical" in entry for entry in contract["unresolved"]))

        with_mech = self.gate(complete_input())
        mechanical = [entry for entry in with_mech["constraints"] if entry["kind"] == "mechanical"]
        self.assertEqual(len(mechanical), 1)
        self.assertEqual(mechanical[0]["boardSizeMm"], {"widthMm": 60, "heightMm": 40})

    def test_missing_description_and_acceptance_criteria_are_flagged(self):
        requirements = complete_input()
        del requirements["description"]
        del requirements["acceptanceCriteria"]
        contract = self.gate(requirements)
        self.assertEqual(contract["status"], "requirements-incomplete")
        text = "\n".join(contract["unresolved"])
        self.assertIn("goal:缺少目标描述(description)", text)
        self.assertIn("goal:缺少最小成功标准(acceptanceCriteria)", text)
        self.assertIsNone(contract["board"]["projectName"])

    def test_no_third_party_imports(self):
        source = (SPEC_DIR / "requirements_gate.py").read_text(encoding="utf-8")
        for banned in ("jsonschema", "import yaml", "requests", "numpy", "pandas"):
            self.assertNotIn(banned, source)
        for banned in ("jsonschema", "yaml", "requests", "numpy", "pandas"):
            self.assertNotIn(banned, sys.modules)

    def test_validate_requirements_input_returns_input_unchanged(self):
        requirements = complete_input()
        validated = validate_requirements_input(requirements)
        self.assertIs(validated, requirements)

    def test_input_schema_document_is_loadable(self):
        schema = json.loads((SCHEMA_DIR / "requirements-input.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["kind"]["const"], "jlceda-requirements-input/1.0")
        self.assertTrue(schema["additionalProperties"] is False)

    def test_cli_writes_contract_and_rejects_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = root / "requirements.json"
            output_path = root / "contract.json"
            input_path.write_text(json.dumps(complete_input()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--input", str(input_path), "--output", str(output_path), "--now", FIXED_NOW],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            contract = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(contract["kind"], "hardware-contract")
            self.assertEqual(contract["status"], "requirements-complete")
            self.assertEqual(contract["generatedAt"], FIXED_NOW)
            self.assertEqual(contract["unresolved"], [])

            bad_input = root / "bad.json"
            bad_output = root / "rejected.json"
            bad_input.write_text(
                json.dumps({"schemaVersion": "1.0.0", "kind": "jlceda-requirements-input/1.0", "powerInput": {"minVoltageV": 6, "maxVoltageV": 5}}),
                encoding="utf-8",
            )
            rejected = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--input", str(bad_input), "--output", str(bad_output)],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertFalse(bad_output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
