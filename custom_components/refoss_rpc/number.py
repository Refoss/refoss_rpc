"""Number entities for Refoss."""

from __future__ import annotations

from typing import Any

from aiorefoss.exceptions import DeviceConnectionError, InvalidAuthError, RpcCallError

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import LOGGER
from .coordinator import RefossConfigEntry, RefossCoordinator
from .entity import RefossEntity

SUPPORTED_MODELS = ("em01p", "em06p", "em16p")
PUSH_INTERVAL_MIN = 1
PUSH_INTERVAL_MAX = 15


def _parse_push_interval(value: Any) -> int | None:
    """Return a supported interval, or None when the device value is unusable."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not float(value).is_integer()
        or not PUSH_INTERVAL_MIN <= int(value) <= PUSH_INTERVAL_MAX
    ):
        return None
    return int(value)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: RefossConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up configurable Refoss values."""
    coordinator = config_entry.runtime_data.coordinator
    if not coordinator or not coordinator.device.initialized:
        return

    model = f"{coordinator.device.model} {coordinator.model}".casefold()
    if not any(supported_model in model for supported_model in SUPPORTED_MODELS):
        return

    try:
        config = await coordinator.device.call_rpc("Sys.Config.Get")
    except (DeviceConnectionError, InvalidAuthError, RpcCallError) as err:
        LOGGER.debug(
            "Unable to read data reporting interval for %s: %r",
            coordinator.name,
            err,
        )
        return

    device_config = config.get("device") if isinstance(config, dict) else None
    if not isinstance(device_config, dict) or "push_interval" not in device_config:
        LOGGER.debug(
            "Data reporting interval is not supported by %s firmware %s",
            coordinator.name,
            coordinator.device.firmware_version,
        )
        return

    push_interval = _parse_push_interval(device_config["push_interval"])
    if push_interval is None:
        LOGGER.warning(
            "Ignoring invalid push_interval %r returned by %s",
            device_config["push_interval"],
            coordinator.name,
        )
        return

    async_add_entities([RefossDataReportingInterval(coordinator, push_interval)])


class RefossDataReportingInterval(RefossEntity, NumberEntity):
    """Configure how often an energy monitor pushes status data."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_native_max_value = PUSH_INTERVAL_MAX
    _attr_native_min_value = PUSH_INTERVAL_MIN
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_translation_key = "data_reporting_interval"

    def __init__(self, coordinator: RefossCoordinator, value: int) -> None:
        """Initialize the data reporting interval entity."""
        super().__init__(coordinator, "data_reporting_interval")
        self._attr_name = "Data reporting interval"
        self._attr_native_value = value

    async def async_set_native_value(self, value: float) -> None:
        """Set the device status push interval."""
        if (
            isinstance(value, bool)
            or not float(value).is_integer()
            or not PUSH_INTERVAL_MIN <= int(value) <= PUSH_INTERVAL_MAX
        ):
            raise HomeAssistantError(
                f"Data reporting interval must be an integer from "
                f"{PUSH_INTERVAL_MIN} to {PUSH_INTERVAL_MAX} seconds"
            )

        interval = int(value)
        await self.call_rpc(
            "Sys.Config.Set",
            {"config": {"device": {"push_interval": interval}}},
        )

        config = await self.call_rpc("Sys.Config.Get", None)
        device_config = config.get("device") if isinstance(config, dict) else None
        confirmed_interval = (
            _parse_push_interval(device_config.get("push_interval"))
            if isinstance(device_config, dict)
            else None
        )
        if confirmed_interval != interval:
            raise HomeAssistantError(
                "The device did not apply the data reporting interval. "
                f"Requested {interval} seconds, device returned "
                f"{confirmed_interval!r}."
            )

        self._attr_native_value = confirmed_interval
        self.async_write_ha_state()
