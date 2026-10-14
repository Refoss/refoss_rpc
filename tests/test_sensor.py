"""Regression tests for Refoss energy counter filtering.

Run with ``python -m unittest discover -s tests -v``. The repository has no HA
unit-test environment, so load the actual sensor class from its source AST with
lightweight entity bases. This isolates the counter filter without copying it
or requiring a running Home Assistant instance.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class AttributeEntity:
    """Supply the coordinator-backed value and description used by the filter."""

    def __init__(self, coordinator, key, attribute, description):
        self.entity_description = description
        self.attribute_value = None


class SensorEntity:
    """Stand in for the unrelated Home Assistant entity base."""


SOURCE = Path(__file__).resolve().parents[1] / "custom_components/refoss_rpc/sensor.py"
TREE = ast.parse(SOURCE.read_text())
SENSOR_CLASS = next(
    node for node in TREE.body
    if isinstance(node, ast.ClassDef) and node.name == "RefossSensor"
)
NAMESPACE = {
    "RefossAttributeEntity": AttributeEntity,
    "SensorEntity": SensorEntity,
    "SensorStateClass": SimpleNamespace(TOTAL_INCREASING="total_increasing"),
    "time": SimpleNamespace(monotonic=lambda: 0),
}
MODULE = ast.Module(
    body=[
        ast.ImportFrom(
            module="__future__", names=[ast.alias(name="annotations")], level=0
        ),
        SENSOR_CLASS,
    ],
    type_ignores=[],
)
exec(compile(ast.fix_missing_locations(MODULE), str(SOURCE), "exec"), NAMESPACE)
RefossSensor = NAMESPACE["RefossSensor"]


class CounterFilterTests(unittest.TestCase):
    """Exercise startup and runtime readings with a deterministic clock."""

    def setUp(self):
        self.sensor = RefossSensor(
            None, "em:0", "em_month_energy",
            SimpleNamespace(state_class="total_increasing"),
        )

    def read(self, value, elapsed):
        self.sensor.attribute_value = value
        with patch.object(NAMESPACE["time"], "monotonic", return_value=elapsed):
            return self.sensor.native_value

    def test_startup_zero_recovers_without_publishing_a_reset(self):
        self.assertIsNone(self.read(0.0, 0))
        self.assertIsNone(self.read(0.0, 12))
        self.assertEqual(self.read(10.0, 14), 10.0)
        self.assertEqual(self.read(10.001, 15), 10.001)

    def test_unused_channel_zero_is_eventually_published(self):
        self.assertIsNone(self.read(0, 0))
        self.assertIsNone(self.read(0, 59))
        self.assertEqual(self.read(0, 60), 0)
        self.assertEqual(self.read(0, 61), 0)
        self.assertEqual(self.read(0.001, 62), 0.001)

    def test_initial_positive_value_is_published_immediately(self):
        self.assertEqual(self.read(10.0, 0), 10.0)
        self.assertEqual(self.read(10.001, 1), 10.001)

    def test_new_period_can_start_with_positive_usage(self):
        self.assertIsNone(self.read(0, 0))
        self.assertEqual(self.read(0.001, 1), 0.001)

    def test_recovery_clears_the_startup_confirmation_window(self):
        self.assertIsNone(self.read(0, 0))
        self.assertEqual(self.read(10.0, 10), 10.0)
        self.assertEqual(self.read(0, 59), 10.0)
        self.assertEqual(self.read(0, 60), 10.0)
        self.assertEqual(self.read(0, 119), 0)

    def test_runtime_transient_zero_still_uses_previous_value(self):
        self.assertEqual(self.read(10.0, 0), 10.0)
        self.assertEqual(self.read(0, 10), 10.0)
        self.assertEqual(self.read(10.001, 24), 10.001)

    def test_genuine_runtime_reset_still_reaches_statistics(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(0, 10), 10.0)
        self.assertEqual(self.read(0.001, 69), 10.0)
        self.assertEqual(self.read(0.002, 70), 0.002)

    def test_missing_value_does_not_create_a_numeric_baseline(self):
        self.assertIsNone(self.read(None, 0))
        self.assertIsNone(self.read(0, 10))
        self.assertEqual(self.read(10.0, 24), 10.0)

    def test_non_increasing_sensors_keep_their_zero_readings(self):
        for state_class in ("measurement", "total", None):
            with self.subTest(state_class=state_class):
                self.sensor.entity_description.state_class = state_class
                self.assertEqual(self.read(0, 0), 0)


if __name__ == "__main__":
    unittest.main()
