from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "personal-finance-planner"
MCP_ROOT = PLUGIN_ROOT / "mcp"
sys.path.insert(0, str(MCP_ROOT))

from personal_finance_planner.calculator import calculate_fi


class PluginIdentityTests(unittest.TestCase):
    def test_public_name_changes_without_breaking_technical_id(self) -> None:
        # Given: the standalone repository manifests.
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )

        # When: identity fields are compared across both manifests.
        entry = marketplace["plugins"][0]

        # Then: the public scope is narrower while installed identifiers stay compatible.
        self.assertEqual(manifest["name"], "personal-finance-planner")
        self.assertEqual(manifest["interface"]["displayName"], "Personal Finance Planner")
        self.assertEqual(manifest["version"], "0.9.0-rc.1")
        self.assertLessEqual(len(manifest["interface"]["defaultPrompt"]), 3)
        self.assertEqual(entry["name"], "personal-finance-planner")
        self.assertEqual(entry["source"]["path"], "./plugins/personal-finance-planner")
        self.assertEqual(marketplace["name"], "personal-finance-planner")

    def test_mcp_display_name_matches_the_plugin(self) -> None:
        # Given: the package-local MCP entry point.
        specification = importlib.util.spec_from_file_location(
            "personal_finance_planner_mcp_server",
            MCP_ROOT / "server.py",
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)

        # When: the MCP server module is loaded.
        specification.loader.exec_module(module)

        # Then: its user-facing name matches the Plugin identity.
        self.assertEqual(module.mcp.name, "Personal Finance Planner")


class PluginBehaviorTests(unittest.TestCase):
    def test_financial_independence_calculation_is_deterministic(self) -> None:
        # Given: a wholly synthetic FI scenario.
        inputs = {
            "birth_year": 1988,
            "base_year": 2026,
            "target_year": 2036,
            "annual_spending_scenarios_cny": [96000],
            "current_investable_assets_cny": 740000,
            "withdrawal_rates_pct": [4.0],
            "real_return_rates_pct": [0.0],
        }

        # When: the deterministic calculator runs.
        result = calculate_fi(**inputs)

        # Then: the exact capital target follows the declared contract.
        self.assertEqual(result["capital_targets"][0]["capital_target_cny"], 2400000.0)
        self.assertFalse(result["capital_targets"][0]["current_surplus_cny"])

    def test_all_yaml_evaluations_are_synthetic(self) -> None:
        # Given: every distributed YAML evaluation file.
        fixtures = sorted((PLUGIN_ROOT / "evals").glob("*.yaml"))

        # When: their release classifications are read.
        classifications = {
            path.name: yaml.safe_load(path.read_text(encoding="utf-8"))[
                "fixture_classification"
            ]
            for path in fixtures
        }

        # Then: no personal or derived-real fixture is packaged.
        self.assertTrue(fixtures)
        self.assertEqual(set(classifications.values()), {"synthetic"})


if __name__ == "__main__":
    unittest.main()
