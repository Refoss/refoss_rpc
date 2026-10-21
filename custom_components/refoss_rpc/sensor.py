"""Sensor entities for Refoss."""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import LOGGER
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


class RefossSensor(RefossAttributeEntity, RestoreSensor):
    """Refoss sensor entity."""

    entity_description: RefossSensorDescription

    # 抖动容忍度：回退幅度小于该比例（20%）视为固件抖动/舍入误差，保持上次值不发布。
    # 比 HA recorder 的 10% 复位判定（0.9 阈值）更宽，这个区间内的回退不会被记成新周期
    _JITTER_TOLERANCE = 0.2
    # 周期归零判定：大幅下降时，值不超过上次值的该比例才视为日/周/月归零的起点；
    # 偏低但不接近 0 的值（通道未汇总齐、设备恢复了旧计数）按住上次值
    _RESET_NEAR_ZERO_RATIO = 0.05
    # 归零确认窗口（秒）：从接近 0 的起点开始，低位持续超过该时长才发布，
    # 防护设备重启后数分钟内持续上报 0 值
    _RESET_CONFIRM_SECONDS = 300
    # 偏低值最长按住时长（秒）：期间读数不再下降，超时后按新周期接受，
    # 避免漏掉归零起点（或 HA 停机跨周期）后永久冻结
    _LOW_HOLD_MAX_SECONDS = 1800
    # 大幅上涨判定：超过上次值该比例的上涨需下一次读数确认，过滤单帧尖峰
    _SPIKE_RATIO = 0.2
    # 尖峰的最小绝对增量：低于该增量的上涨直接放行，避免周期刚归零、基线很小时
    # 正常累计也被逐帧按住。Wh 为插座：3.7 kW 满载 2 分钟约 123 Wh；
    # kWh 为整屋电表：25 kW 满载 1 分钟约 0.42 kWh
    _SPIKE_MIN_DELTA = {
        UnitOfEnergy.WATT_HOUR: 150.0,
        UnitOfEnergy.KILO_WATT_HOUR: 0.5,
    }
    # 生涯累计计数器不会周期归零，下降一律走按住逻辑，不进入归零确认窗
    _LIFETIME_SUB_KEYS = frozenset({"total_energy", "total_ret_energy"})
    # 生涯计数器偏低值最长按住时长（秒）：平稳低位持续一天才按计数器重置接受
    # （设备恢复出厂、更换计量模块），避免实体永久冻结
    _LIFETIME_HOLD_MAX_SECONDS = 86400

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
        self._holding_low_since: float | None = None
        self._holding_low_floor: float | None = None
        self._pending_rise: float | None = None
        self._counter_value: StateType = None

    @property
    def _is_counter(self) -> bool:
        return self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING

    def _clear_pending_drop(self) -> None:
        self._pending_reset_since = None
        self._holding_low_since = None
        self._holding_low_floor = None

    def _accept(self, value: float) -> float:
        """Publish value as the new baseline and clear all pending checks."""
        self._clear_pending_drop()
        self._pending_rise = None
        self._last_reported = value
        return value

    async def async_added_to_hass(self) -> None:
        """Restore the last reported total as the drop-detection baseline."""
        await super().async_added_to_hass()
        if not self._is_counter:
            return
        if (last_data := await self.async_get_last_sensor_data()) is not None:
            restored = last_data.native_value
            if (
                last_data.native_unit_of_measurement == self.native_unit_of_measurement
                and not isinstance(restored, bool)
                and isinstance(restored, (int, float, Decimal))
                and (restored_value := float(restored)) > 0
            ):
                self._last_reported = restored_value
        self._update_counter_value()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Run the counter filter once per device update, then write state."""
        if self._is_counter:
            self._update_counter_value()
        super()._handle_coordinator_update()

    def _update_counter_value(self) -> None:
        self._counter_value = self._filter_counter(self.attribute_value)

    @property
    def native_value(self) -> StateType:
        """Return value of sensor."""
        # The counter filter is stateful, so it must not run on incidental
        # reads such as the periodic restore-state dump.
        if self._is_counter:
            return self._counter_value
        return self.attribute_value

    def _filter_counter(self, value: StateType) -> StateType:
        """Filter a total_increasing reading against the last published value."""
        last = self._last_reported
        if not isinstance(value, (int, float)):
            # 读不到的那一帧保持上次值，避免状态在数值和 unknown 之间来回切换
            return last

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

        # 上一帧是待确认的大幅上涨：本帧不低于它的 (1 - 20%) 才算确认，
        # 否则丢弃那一帧，本帧照常走下面的判定
        rise_confirmed = False
        if self._pending_rise is not None:
            rise_confirmed = value >= self._pending_rise * (1 - self._SPIKE_RATIO)
            self._pending_rise = None

        if not isinstance(last, (int, float)) or last <= 0 or value >= last:
            # 大幅上涨（超过上次值 20%）先按住一帧，单帧尖峰不会成为基线
            if (
                isinstance(last, (int, float))
                and last > 0
                and not rise_confirmed
                and value > last * (1 + self._SPIKE_RATIO)
                and value - last
                > self._SPIKE_MIN_DELTA.get(self.native_unit_of_measurement, 0.0)
            ):
                self._pending_rise = value
                LOGGER.debug(
                    "Holding rise of %s from %s to %s until the next reading",
                    self.entity_id,
                    last,
                    value,
                )
                return last
            # 正常递增 / 无历史基准 / 已确认的上涨：直接放行。
            # 设备重启瞬态的恢复值也在此放行：
            # 低位被按住期间 last 未被拉低，恢复值 >= last 直接发布，
            # HA 只见 3.737 → 3.746，不会产生虚假尖峰。
            return self._accept(value)

        # ---- value < last 且 last > 0：出现下降 ----
        drop_ratio = (last - value) / last

        # 场景1：小幅抖动（固件重算/舍入误差，降幅 < 20%）→ 保持上次值，
        # 保证 total_increasing 语义下的严格递增，recorder 告警消失。
        # 读数已回到上次值附近，之前的归零/偏低计时作废，否则后续偏低值会沿用旧计时被误接受
        if drop_ratio < self._JITTER_TOLERANCE:
            self._clear_pending_drop()
            return last

        # 场景2：大幅下降但起点不接近 0（或生涯累计计数器）→ 不是周期归零，按住上次值。
        # 已进入归零确认窗时，窗口内值从 0 附近回升属于正常累计，不在此拦截
        lifetime = self.entity_description.sub_key in self._LIFETIME_SUB_KEYS
        if self._pending_reset_since is None and (
            lifetime or value > last * self._RESET_NEAR_ZERO_RATIO
        ):
            now = time.monotonic()
            if self._holding_low_since is None:
                self._holding_low_since = now
                self._holding_low_floor = value
                LOGGER.warning(
                    "Ignoring drop of %s from %s to %s; holding last value until it"
                    " recovers or a new cycle is confirmed",
                    self.entity_id,
                    last,
                    value,
                )
                return last

            if self._holding_low_floor is not None and value < self._holding_low_floor:
                # 按住期间读数还在下降，说明是乱跳的错值：重新计时
                self._holding_low_since = now
            self._holding_low_floor = value

            max_hold = (
                self._LIFETIME_HOLD_MAX_SECONDS if lifetime else self._LOW_HOLD_MAX_SECONDS
            )
            if now - self._holding_low_since < max_hold:
                return last

            if lifetime:
                LOGGER.warning(
                    "Accepting %s as a counter reset for %s after holding %s for %s"
                    " seconds",
                    value,
                    self.entity_id,
                    last,
                    max_hold,
                )
            else:
                # 偏低值平稳持续超过最长按住时长 → 按新周期接受（例如漏掉了归零起点）
                LOGGER.info(
                    "Accepting %s as a new cycle for %s after holding %s for %s seconds",
                    value,
                    self.entity_id,
                    last,
                    max_hold,
                )
            return self._accept(value)

        # 场景3：降到接近 0 → 疑似周期归零，进入确认窗口
        now = time.monotonic()
        if self._pending_reset_since is None:
            # 首次见到接近 0 的低位：按住不发，开始计时
            self._pending_reset_since = now
            self._holding_low_since = None
            self._holding_low_floor = None
            return last

        if now - self._pending_reset_since < self._RESET_CONFIRM_SECONDS:
            # 低位未持续足够久（设备重启后报 0 通常数分钟内恢复）：继续按住
            return last

        # 低位持续超过窗口 → 确认为真实周期重置（日/周/月归零），发布，
        # HA 正常记录 reset，仅延迟一个确认窗口（5 分钟）
        return self._accept(value)
