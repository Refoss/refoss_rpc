"""Refoss entity helper."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from aiorefoss.exceptions import DeviceConnectionError, InvalidAuthError, RpcCallError

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import LOGGER
from .coordinator import RefossConfigEntry, RefossCoordinator
from .utils import (
    async_remove_refoss_entity,
    get_refoss_entity_name,
    get_refoss_key_instances,
    merge_channel_get_status,
)


@callback
def async_setup_entry_refoss(
    hass: HomeAssistant,
    config_entry: RefossConfigEntry,
    async_add_entities: AddEntitiesCallback,
    sensors: Mapping[str, RefossEntityDescription],
    sensor_class: Callable,
) -> None:
    """Set up entities for  Refoss."""
    coordinator = config_entry.runtime_data.coordinator
    # If the device is not initialized, return directly
    if not coordinator or not coordinator.device.initialized:
        return

    device_status = coordinator.device.status
    device_config = coordinator.device.config
    mac = coordinator.mac
    entities: list[Any] = []

    for sensor_id, description in sensors.items():
        key_instances = get_refoss_key_instances(device_status, description.key)

        for key in key_instances:
            key_status = device_status.get(key)
            if key_status is None:
                continue

            # Filter out sensors that are not supported or do not match the configuration
            if (
                not key.startswith("emmerge:")
                and description.sub_key not in key_status
                and not description.supported(key_status)
            ):
                continue

            # Filter and remove entities that should not be created according to the configuration/status
            if description.removal_condition and description.removal_condition(
                device_config, device_status, key
            ):
                try:
                    domain = sensor_class.__module__.split(".")[-1]
                except AttributeError:
                    LOGGER.error(
                        "Failed to get module name from sensor_class for sensor_id %s and key %s",
                        sensor_id,
                        key,
                    )
                    continue
                unique_id = f"{mac}-{key}-{sensor_id}"
                async_remove_refoss_entity(hass, domain, unique_id)
            else:
                entities.append(sensor_class(coordinator, key, sensor_id, description))

    if entities:
        async_add_entities(entities)


@dataclass(frozen=True, kw_only=True)
class RefossEntityDescription(EntityDescription):
    """Class to describe a  entity."""

    name: str = ""
    sub_key: str

    value: Callable[[Any, Any], Any] | None = None
    removal_condition: Callable[[dict, dict, str], bool] | None = None
    supported: Callable = lambda _: False


class RefossEntity(CoordinatorEntity[RefossCoordinator]):
    """Helper class to represent a entity."""

    def __init__(self, coordinator: RefossCoordinator, key: str) -> None:
        """Initialize Refoss entity."""
        super().__init__(coordinator)
        self.key = key
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, coordinator.mac)}
        )
        self._attr_unique_id = f"{coordinator.mac}-{key}"
        self._attr_name = get_refoss_entity_name(coordinator.device, key)

    @property
    def available(self) -> bool:
        """Check if device is available and initialized."""
        coordinator = self.coordinator
        return super().available and (coordinator.device.initialized)

    @property
    def status(self) -> dict | None:
        """Device status by entity key."""
        device_status = self.coordinator.device.status.get(self.key)
        if device_status is None:
            LOGGER.debug("Device status not found for key: %s", self.key)
        return device_status

    async def async_added_to_hass(self) -> None:
        """When entity is added to HASS."""
        self.async_on_remove(self.coordinator.async_add_listener(self._update_callback))

    @callback
    def _update_callback(self) -> None:
        """Handle device update."""
        self.async_write_ha_state()

    async def call_rpc(self, method: str, params: Any) -> Any:
        """Call RPC method."""
        LOGGER.debug(
            "Call RPC for entity %s, method: %s, params: %s",
            self.name,
            method,
            params,
        )
        try:
            return await self.coordinator.device.call_rpc(method, params)
        except DeviceConnectionError as err:
            self.coordinator.last_update_success = False
            raise HomeAssistantError(
                f"Call RPC for {self.name} connection error, method: {method}, params:"
                f" {params}, error: {err!r}"
            ) from err
        except RpcCallError as err:
            raise HomeAssistantError(
                f"Call RPC for {self.name} request error, method: {method}, params:"
                f" {params}, error: {err!r}"
            ) from err
        except InvalidAuthError:
            await self.coordinator.async_shutdown_device_and_start_reauth()


class RefossAttributeEntity(RefossEntity, Entity):
    """Helper class to represent a attribute."""

    entity_description: RefossEntityDescription

    def __init__(
        self,
        coordinator: RefossCoordinator,
        key: str,
        attribute: str,
        description: RefossEntityDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, key)
        self.attribute = attribute
        self.entity_description = description

        self._attr_unique_id = f"{super().unique_id}-{attribute}"
        self._attr_name = get_refoss_entity_name(
            device=coordinator.device, key=key, description=description.name
        )
        self._last_value = None

    @property
    def sub_status(self) -> Any | None:
        """Get the sub - status of the device by entity key.

        Returns the value corresponding to the sub - key in the device status.
        If the device status is None or the sub - key does not exist, returns None.
        """
        device_status = self.status
        if device_status is None:
            LOGGER.debug("Device status is None for entity %s", self.name)
            return None
        sub_key = self.entity_description.sub_key
        sub_status = device_status.get(sub_key)
        return sub_status

    @property
    def attribute_value(self) -> StateType:
        """Value of sensor."""
        try:
            if self.key.startswith("emmerge:"):
                # Call the merge channel attributes function
                return merge_channel_get_status(
                    self.coordinator.device.status,
                    self.key,
                    self.entity_description.sub_key,
                )

            # Reduce repeated calls and get the sub-status
            sub_status = self.sub_status

            if self.entity_description.value is not None:
                # Call the custom value processing function
                self._last_value = self.entity_description.value(
                    sub_status, self._last_value
                )
            else:
                self._last_value = sub_status

            return self._last_value
        except Exception as e:
            # Log the exception
            LOGGER.error(
                "Error getting attribute value for entity %s, key %s, attribute %s: %s",
                self.name,
                self.key,
                self.attribute,
                str(e),
            )
            return None
