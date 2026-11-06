"""Config flow for Refoss RPC integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aiorefoss.common import (
    ConnectionOptions,
    fmt_macaddress,
    get_info,
    get_info_auth,
    mac_address_from_name,
)
from aiorefoss.exceptions import (
    DeviceConnectionError,
    InvalidAuthError,
    MacAddressMismatchError,
)
from aiorefoss.rpc_device import RpcDevice
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import DEFAULT_PORT, DOMAIN, LOGGER
from .coordinator import async_reconnect_soon
from .utils import get_configuration_url

INTERNAL_WIFI_AP_IP = "10.10.10.1"
PORT_SCHEMA = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))


async def async_validate_input(
    hass: HomeAssistant,
    host: str,
    port: int,
    info: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    options = ConnectionOptions(
        ip_address=host,
        username=data.get(CONF_USERNAME),
        password=data.get(CONF_PASSWORD),
        device_mac=info[CONF_MAC],
        port=port,
    )

    device = await RpcDevice.create(
        async_get_clientsession(hass),
        options,
    )
    try:
        await device.initialize()
    finally:
        await device.shutdown()

    return {
        "name": device.name,
        "model": device.model,
    }


class RefossConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for refoss rpc."""

    VERSION = 1
    MINOR_VERSION = 1

    host: str = ""
    port: int = DEFAULT_PORT
    info: dict[str, Any] = {}
    device_info: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            try:
                self.info = await self._async_get_info(host, port)
            except DeviceConnectionError:
                errors["base"] = "cannot_connect"
            else:
                mac = fmt_macaddress(self.info[CONF_MAC])
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured(
                    {CONF_HOST: host, CONF_PORT: port}
                )
                self.host = host
                self.port = port
                if get_info_auth(self.info):
                    return await self.async_step_credentials()

                try:
                    device_info = await async_validate_input(
                        self.hass, host, port, self.info, {}
                    )
                except DeviceConnectionError:
                    errors["base"] = "cannot_connect"
                except MacAddressMismatchError:
                    errors["base"] = "mac_address_mismatch"
                else:
                    if device_info["model"]:
                        return self.async_create_entry(
                            title=device_info["name"],
                            data={
                                CONF_MAC: self.info[CONF_MAC],
                                CONF_HOST: self.host,
                                CONF_PORT: self.port,
                                "model": device_info["model"],
                            },
                        )
                    errors["base"] = "firmware_not_fully_supported"

        schema = {
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): PORT_SCHEMA,
        }
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the credentials step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_USERNAME] = "admin"
            try:
                device_info = await async_validate_input(
                    self.hass, self.host, self.port, self.info, user_input
                )
            except InvalidAuthError:
                errors["base"] = "invalid_auth"
            except DeviceConnectionError:
                errors["base"] = "cannot_connect"
            except MacAddressMismatchError:
                errors["base"] = "mac_address_mismatch"
            else:
                if device_info["model"]:
                    return self.async_create_entry(
                        title=device_info["name"],
                        data={
                            **user_input,
                            CONF_MAC: self.info[CONF_MAC],
                            CONF_HOST: self.host,
                            CONF_PORT: self.port,
                            "model": device_info["model"],
                        },
                    )
                errors["base"] = "firmware_not_fully_supported"
        else:
            user_input = {}

        schema = {
            vol.Required(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")): str,
        }
        return self.async_show_form(
            step_id="credentials", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle configuration by re-auth."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""

        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        host = reauth_entry.data[CONF_HOST]
        port = reauth_entry.data.get(CONF_PORT, DEFAULT_PORT)

        if user_input is not None:
            try:
                info = await self._async_get_info(host, port)
            except (DeviceConnectionError, InvalidAuthError):
                return self.async_abort(reason="reauth_unsuccessful")

            user_input[CONF_USERNAME] = "admin"
            try:
                await async_validate_input(self.hass, host, port, info, user_input)
            except (DeviceConnectionError, InvalidAuthError):
                return self.async_abort(reason="reauth_unsuccessful")
            except MacAddressMismatchError:
                return self.async_abort(reason="mac_address_mismatch")

            return self.async_update_reload_and_abort(
                reauth_entry, data_updates=user_input
            )

        schema = {
            vol.Required(CONF_PASSWORD): str,
        }

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a flow initialized by zeroconf discovery."""
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT
        if mac := mac_address_from_name(discovery_info.name):
            await self._async_discovered_mac(mac, host, port)
        try:
            self.info = await self._async_get_info(host, port)
        except DeviceConnectionError:
            return self.async_abort(reason="cannot_connect")
        if not mac:
            mac = fmt_macaddress(self.info[CONF_MAC])
            await self._async_discovered_mac(mac, host, port)

        self.host = host
        self.port = port
        self.context.update(
            {
                "title_placeholders": {"name": self.info["name"]},
                "configuration_url": get_configuration_url(host, port),
            }
        )

        if get_info_auth(self.info):
            return await self.async_step_credentials()
        try:
            self.device_info = await async_validate_input(
                self.hass, self.host, self.port, self.info, {}
            )
        except DeviceConnectionError:
            return self.async_abort(reason="cannot_connect")
        except MacAddressMismatchError:
            return self.async_abort(reason="mac_address_mismatch")

        return await self.async_step_confirm_discovery()

    async def async_step_confirm_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle discovery confirm."""
        errors: dict[str, str] = {}

        if not self.device_info["model"]:
            errors["base"] = "firmware_not_fully_supported"
            model = "Refoss"
        else:
            model = self.device_info["model"]
            if user_input is not None:
                return self.async_create_entry(
                    title=self.device_info["name"],
                    data={
                        CONF_MAC: self.info[CONF_MAC],
                        CONF_HOST: self.host,
                        CONF_PORT: self.port,
                        "model": model,
                    },
                )
            self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm_discovery",
            description_placeholders={
                "model": model,
                "host": get_configuration_url(self.host, self.port),
            },
            errors=errors,
        )

    async def _async_discovered_mac(self, mac: str, host: str, port: int) -> None:
        """Handle an already-configured device found through discovery."""
        if (
            current_entry := await self.async_set_unique_id(mac)
        ) and current_entry.data.get(CONF_HOST) == host:
            LOGGER.debug(
                "async_reconnect_soon: host: %s, port: %s, mac: %s",
                host,
                port,
                mac,
            )
            await async_reconnect_soon(self.hass, current_entry)
        if host == INTERNAL_WIFI_AP_IP:
            self._abort_if_unique_id_configured()
        else:
            self._abort_if_unique_id_configured(
                {CONF_HOST: host, CONF_PORT: port}
            )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        errors = {}
        reconfigure_entry = self._get_reconfigure_entry()
        self.host = reconfigure_entry.data[CONF_HOST]
        self.port = reconfigure_entry.data.get(CONF_PORT, DEFAULT_PORT)
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            try:
                info = await self._async_get_info(host, port)
            except DeviceConnectionError:
                errors["base"] = "cannot_connect"
            else:
                mac = fmt_macaddress(info[CONF_MAC])
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_mismatch(reason="another_device")

                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self.host): str,
                    vol.Optional(CONF_PORT, default=self.port): PORT_SCHEMA,
                }
            ),
            description_placeholders={"device_name": reconfigure_entry.title},
            errors=errors,
        )

    async def _async_get_info(self, host: str, port: int) -> dict[str, Any]:
        """Get info from refoss device."""
        return await get_info(async_get_clientsession(self.hass), host, port=port)
