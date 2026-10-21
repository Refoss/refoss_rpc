"""Regression tests for Refoss energy counter filtering.

Run with ``python -m unittest discover -s tests -v``. The repository has no HA
unit-test environment, so load the actual sensor class from its source AST with
lightweight entity bases. This isolates the counter filter without copying it
or requiring a running Home Assistant instance.
"""

from __future__ import annotations

import ast
from decimal import Decimal
import logging
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class AttributeEntity:
    """Supply the coordinator-backed value and description used by the filter."""

    def __init__(self, coordinator, key, attribute, description):
        self.entity_description = description
        self.native_unit_of_measurement = description.native_unit_of_measurement
        self.entity_id = f"sensor.{attribute}"
        self.attribute_value = None


class RestoreSensor:
    """Stand in for the Home Assistant sensor and coordinator entity bases."""

    def _handle_coordinator_update(self):
        """The real base writes state; nothing to do here."""


SOURCE = Path(__file__).resolve().parents[1] / "custom_components/refoss_rpc/sensor.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
SENSOR_CLASS = next(
    node for node in TREE.body
    if isinstance(node, ast.ClassDef) and node.name == "RefossSensor"
)
NAMESPACE = {
    "RefossAttributeEntity": AttributeEntity,
    "RestoreSensor": RestoreSensor,
    "SensorStateClass": SimpleNamespace(TOTAL_INCREASING="total_increasing"),
    "UnitOfEnergy": SimpleNamespace(WATT_HOUR="Wh", KILO_WATT_HOUR="kWh"),
    "Decimal": Decimal,
    "LOGGER": logging.getLogger("refoss_rpc.test"),
    "callback": lambda func: func,
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


def make_sensor(sub_key="month_energy", unit="kWh"):
    return RefossSensor(
        None, "em:1", sub_key,
        SimpleNamespace(
            state_class="total_increasing",
            sub_key=sub_key,
            native_unit_of_measurement=unit,
        ),
    )


class CounterFilterTests(unittest.TestCase):
    """Exercise startup and runtime readings with a deterministic clock."""

    def setUp(self):
        self.sensor = make_sensor()

    def read(self, value, elapsed):
        self.sensor.attribute_value = value
        with patch.object(NAMESPACE["time"], "monotonic", return_value=elapsed):
            self.sensor._handle_coordinator_update()
        return self.sensor.native_value

    def test_startup_zero_recovers_without_publishing_a_reset(self):
        self.assertIsNone(self.read(0.0, 0))
        self.assertIsNone(self.read(0.0, 12))
        self.assertEqual(self.read(10.0, 14), 10.0)
        self.assertEqual(self.read(10.001, 15), 10.001)

    def test_unused_channel_zero_is_eventually_published(self):
        self.assertIsNone(self.read(0, 0))
        self.assertIsNone(self.read(0, 299))
        self.assertEqual(self.read(0, 300), 0)
        self.assertEqual(self.read(0, 301), 0)
        self.assertEqual(self.read(0.001, 302), 0.001)

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
        self.assertEqual(self.read(0, 358), 10.0)
        self.assertEqual(self.read(0, 359), 0)

    def test_runtime_transient_zero_still_uses_previous_value(self):
        self.assertEqual(self.read(10.0, 0), 10.0)
        self.assertEqual(self.read(0, 10), 10.0)
        self.assertEqual(self.read(10.001, 24), 10.001)

    def test_genuine_runtime_reset_still_reaches_statistics(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(0, 10), 10.0)
        self.assertEqual(self.read(0.001, 309), 10.0)
        self.assertEqual(self.read(0.002, 310), 0.002)

    def test_missing_value_does_not_create_a_numeric_baseline(self):
        self.assertIsNone(self.read(None, 0))
        self.assertIsNone(self.read(0, 10))
        self.assertEqual(self.read(10.0, 24), 10.0)

    def test_missing_value_keeps_the_last_published_total(self):
        self.assertEqual(self.read(10.0, 0), 10.0)
        self.assertEqual(self.read(None, 5), 10.0)
        self.assertEqual(self.read(10.1, 10), 10.1)

    def test_non_increasing_sensors_keep_their_zero_readings(self):
        for state_class in ("measurement", "total", None):
            with self.subTest(state_class=state_class):
                self.sensor.entity_description.state_class = state_class
                self.assertEqual(self.read(0, 0), 0)

    def test_extra_reads_do_not_advance_the_filter(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(20.0, 10), 10.0)
        # The restore-state dump reads native_value again for the same frame.
        self.assertEqual(self.sensor.native_value, 10.0)
        self.assertEqual(self.sensor.native_value, 10.0)
        self.assertEqual(self.read(10.01, 20), 10.01)

    def test_low_value_is_accepted_as_new_cycle_after_max_hold(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(5.0, 10), 10.0)
        self.assertEqual(self.read(5.1, 1000), 10.0)
        self.assertEqual(self.read(5.2, 1810), 5.2)

    def test_falling_low_value_restarts_the_hold(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(5.0, 10), 10.0)
        self.assertEqual(self.read(4.0, 1000), 10.0)
        self.assertEqual(self.read(4.1, 1810), 10.0)
        self.assertEqual(self.read(4.2, 2800), 4.2)

    def test_lifetime_counter_drop_is_held_for_a_day(self):
        self.sensor = make_sensor("total_energy")
        self.read(100.0, 0)
        self.assertEqual(self.read(0.1, 10), 100.0)
        self.assertEqual(self.read(0.2, 1810), 100.0)
        self.assertEqual(self.read(0.3, 86409), 100.0)
        self.assertEqual(self.read(0.4, 86410), 0.4)

    def test_single_frame_spike_is_dropped(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(20.0, 10), 10.0)
        self.assertEqual(self.read(10.01, 20), 10.01)

    def test_sustained_rise_is_accepted_on_the_next_reading(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(20.0, 10), 10.0)
        self.assertEqual(self.read(20.1, 20), 20.1)

    def test_small_baseline_growth_is_not_held(self):
        self.read(0.01, 0)
        self.assertEqual(self.read(0.02, 10), 0.02)
        self.assertEqual(self.read(0.05, 20), 0.05)

    def test_watt_hour_spike_threshold_uses_unit(self):
        self.sensor = make_sensor("month_consumption", "Wh")
        self.read(100.0, 0)
        self.assertEqual(self.read(200.0, 10), 200.0)
        self.assertEqual(self.read(400.0, 20), 200.0)

    def test_jitter_cancels_a_pending_reset(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(0, 10), 10.0)
        self.assertEqual(self.read(9.0, 20), 10.0)
        self.assertEqual(self.read(3.0, 410), 10.0)

    def test_jitter_cancels_a_low_value_hold(self):
        self.read(10.0, 0)
        self.assertEqual(self.read(5.0, 10), 10.0)
        self.assertEqual(self.read(9.0, 20), 10.0)
        self.assertEqual(self.read(5.0, 1810), 10.0)


if __name__ == "__main__":
    unittest.main()
