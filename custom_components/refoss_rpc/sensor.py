"""Sensor entities for Refoss."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import RefossConfigEntry, RefossCoordinator
from .entity import (
    RefossAttributeEntity,
    RefossEntityDescription,
    async_setup_entry_refoss,
)
from .utils import get_device_uptime, is_refoss_wifi_stations_disabled


@dataclass(frozen=True, kw_only=True)
class RefossSensorDescription(RefossEntityDescription, SensorEntityDescription):
    """Class to describe a sensor."""


REFOSS_SENSORS: Final = {
    "power": RefossSensorDescription(
        key="switch",
        sub_key="apower",
        name="Power",
        native_unit_of_measurement=UnitOfPower.MILLIWATT,
        value=lambda status, _: None if status is None else float(status),
        suggested_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "voltage": RefossSensorDescription(
        key="switch",
        sub_key="voltage",
        name="Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        value=lambda status, _: None if status is None else float(status),
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "current": RefossSensorDescription(
        key="switch",
        sub_key="current",
        name="Current",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        value=lambda status, _: None if status is None else float(status),
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "energy": RefossSensorDescription(
        key="switch",
        sub_key="month_consumption",
        name="This Month Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "cover_energy": RefossSensorDescription(
        key="cover",
        sub_key="aenergy",
        name="Energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        value=lambda status, _: status["total"],
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    "temperature": RefossSensorDescription(
        key="sys",
        sub_key="temperature",
        name="Device temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda status, _: status["tc"],
        suggested_display_precision=1,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "rssi": RefossSensorDescription(
        key="wifi",
        sub_key="rssi",
        name="RSSI",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        removal_condition=is_refoss_wifi_stations_disabled,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "uptime": RefossSensorDescription(
        key="sys",
        sub_key="uptime",
        name="Uptime",
        value=get_device_uptime,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "em_power": RefossSensorDescription(
        key="em",
        sub_key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "em_voltage": RefossSensorDescription(
        key="em",
        sub_key="voltage",
        name="Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "em_current": RefossSensorDescription(
        key="em",
        sub_key="current",
        name="Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "em_month_energy": RefossSensorDescription(
        key="em",
        sub_key="month_energy",
        name="This Month Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "em_month_ret_energy": RefossSensorDescription(
        key="em",
        sub_key="month_ret_energy",
        name="This Month Return Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(abs(status)),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "em_week_energy": RefossSensorDescription(
        key="em",
        sub_key="week_energy",
        name="This Week Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "em_week_ret_energy": RefossSensorDescription(
        key="em",
        sub_key="week_ret_energy",
        name="This Week Return Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(abs(status)),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "em_day_energy": RefossSensorDescription(
        key="em",
        sub_key="day_energy",
        name="Today Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "em_day_ret_energy": RefossSensorDescription(
        key="em",
        sub_key="day_ret_energy",
        name="Today Return Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(abs(status)),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "em_pf": RefossSensorDescription(
        key="em",
        sub_key="pf",
        name="Power factor",
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "emmerge_power": RefossSensorDescription(
        key="emmerge",
        sub_key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "emmerge_current": RefossSensorDescription(
        key="emmerge",
        sub_key="current",
        name="Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "emmerge_month_energy": RefossSensorDescription(
        key="emmerge",
        sub_key="month_energy",
        name="This Month Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "emmerge_month_ret_energy": RefossSensorDescription(
        key="emmerge",
        sub_key="month_ret_energy",
        name="This Month Return Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(abs(status)),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "emmerge_week_energy": RefossSensorDescription(
        key="emmerge",
        sub_key="week_energy",
        name="This Week Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "emmerge_week_ret_energy": RefossSensorDescription(
        key="emmerge",
        sub_key="week_ret_energy",
        name="This Week Return Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(abs(status)),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "emmerge_day_energy": RefossSensorDescription(
        key="emmerge",
        sub_key="day_energy",
        name="Today Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "emmerge_day_ret_energy": RefossSensorDescription(
        key="emmerge",
        sub_key="day_ret_energy",
        name="Today Return Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(abs(status)),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
      "em_total_energy": RefossSensorDescription(
        key="em",
        sub_key="total_energy",
        name="Total Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(status),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported=lambda status: status.get("total_energy") is not None,
    ),
      "em_total_ret_energy": RefossSensorDescription(
        key="em",
        sub_key="total_ret_energy",
        name="Total Return Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda status, _: None if status is None else float(abs(status)),
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        supported=lambda status: status.get("total_ret_energy") is not None,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: RefossConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors for device."""
    coordinator = config_entry.runtime_data.coordinator
    assert coordinator

    async_setup_entry_refoss(
        hass, config_entry, async_add_entities, REFOSS_SENSORS, RefossSensor
    )


class RefossSensor(RefossAttributeEntity, SensorEntity):
    """Refoss sensor entity."""

    entity_description: RefossSensorDescription

    # 抖动容忍度，对齐 HA recorder 官方 10% 容差（0.9 阈值）：
    # 回退幅度小于该比例视为固件抖动/舍入误差，保持上次值不发布
    _JITTER_TOLERANCE = 0.2
    # 疑似重置的确认窗口（秒），防护设备重启后短暂上报 0 值：
    # 大幅下降需持续低位超过该时长才确认为真实周期重置并发布
    _RESET_CONFIRM_SECONDS = 60

    def __init__(
        self,
        coordinator: RefossCoordinator,
        key: str,
        attribute: str,
        description: RefossSensorDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, key, attribute, description)
        self._last_reported: float | None = None
        self._pending_reset_since: float | None = None

    @property
    def native_value(self) -> StateType:
        """Return value of sensor."""
        value = self.attribute_value

        if self.entity_description.state_class != SensorStateClass.TOTAL_INCREASING:
            return value

        last = self._last_reported
        if not isinstance(value, (int, float)):
            return None

        # Startup has no in-memory baseline. Ignore a brief initial zero so
        # recorder cannot mistake a reconnect placeholder for a counter reset.
        # A genuinely unused or reset counter is accepted after the same
        # confirmation window used for resets during normal operation.
        if last is None and value == 0:
            now = time.monotonic()
            if self._pending_reset_since is None:
                self._pending_reset_since = now
                return None
            if now - self._pending_reset_since < self._RESET_CONFIRM_SECONDS:
                return None

        if not isinstance(last, (int, float)) or last <= 0 or value >= last:
            # 正常递增 / 无历史基准：直接放行。
            # 设备重启瞬态的恢复值也在此放行：
            # 低位被按住期间 last 未被拉低，恢复值 >= last 直接发布，
            # HA 只见 3.737 → 3.746，不会产生虚假尖峰。
            self._pending_reset_since = None
            self._last_reported = value
            return value

        # ---- value < last 且 last > 0：出现下降 ----
        drop_ratio = (last - value) / last

        # 场景1：小幅抖动（固件重算/舍入误差，降幅 < 10%）→ 保持上次值，
        # 保证 total_increasing 语义下的严格递增，recorder 告警消失
        if drop_ratio < self._JITTER_TOLERANCE:
            return last

        # 场景2：大幅下降（降幅 >= 10%）→ 疑似周期重置，进入确认窗口
        now = time.monotonic()
        if self._pending_reset_since is None:
            # 首次见到低位：按住不发，开始计时
            self._pending_reset_since = now
            return last

        if now - self._pending_reset_since < self._RESET_CONFIRM_SECONDS:
            # 低位未持续足够久（设备重启瞬态通常数秒即恢复）：继续按住
            return last

        # 低位持续超过窗口 → 确认为真实周期重置（日/周/月归零），发布，
        # HA 正常记录 reset，仅延迟一个确认窗口（60 秒）
        self._pending_reset_since = None
        self._last_reported = value
        return value
