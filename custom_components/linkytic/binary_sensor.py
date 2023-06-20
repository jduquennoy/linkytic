"""Binary sensors for linkytic integration."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DID_CONNECTION_TYPE,
    DID_CONSTRUCTOR,
    DID_DEFAULT_NAME,
    DID_REGNUMBER,
    DID_TYPE,
    DOMAIN, SETUP_TICMODE, TICMODE_STANDARD,
)
from .serial_reader import LinkyTICReader

_LOGGER = logging.getLogger(__name__)


# config flow setup
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    _LOGGER.debug("%s: setting up binary sensor plateform", config_entry.title)
    # Retrieve the serial reader object
    try:
        serial_reader = hass.data[DOMAIN][config_entry.entry_id]
    except KeyError:
        _LOGGER.error(
            "%s: can not init binaries sensors: failed to get the serial reader object",
            config_entry.title,
        )
        return
    # Wait a bit for the controller to feed on serial frames (home assistant warns after 10s)
    _LOGGER.debug(
        "%s: waiting at most 9s before setting up binary sensor plateform in order for the async serial reader to have time to parse a full frame",
        config_entry.title,
    )
    for i in range(9):
        await asyncio.sleep(1)
        if serial_reader.has_read_full_frame():
            _LOGGER.debug(
                "%s: a full frame has been read, initializing sensors",
                config_entry.title,
            )
            break
        if i == 8:
            _LOGGER.warning(
                "%s: wait time is over but a full frame has yet to be read: initializing sensors anyway",
                config_entry.title,
            )

    # Init sensors
    if config_entry.data.get(SETUP_TICMODE) == TICMODE_STANDARD:
        relays = [RelayState(config_entry.title, uniq_id=config_entry.entry_id, serial_reader=serial_reader, relay_index=i) for i in range(1,9)]
        async_add_entities(relays, True)

    async_add_entities(
        [SerialConnectivity(config_entry.title, config_entry.entry_id, serial_reader)],
        True,
    )


class SerialConnectivity(BinarySensorEntity):
    """Serial connectivity to the Linky TIC serial interface."""

    # Generic properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Connectivité du lien série"
    _attr_should_poll = True

    # Binary sensor properties
    #   https://developers.home-assistant.io/docs/core/entity/binary-sensor/#properties
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self, title: str, uniq_id: str | None, serial_reader: LinkyTICReader
    ) -> None:
        """Initialize the SerialConnectivity binary sensor."""
        _LOGGER.debug("%s: initializing Serial Connectivity binary sensor", title)
        self._title = title
        self._attr_unique_id = f"{DOMAIN}_{uniq_id}_serial_connectivity"
        self._serial_controller = serial_reader
        self._device_uniq_id = uniq_id if uniq_id is not None else "yaml_legacy"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            # connections={(DID_CONNECTION_TYPE, self._serial_controller._port)},
            identifiers={(DOMAIN, self._serial_controller.device_identification[DID_REGNUMBER])},
            manufacturer=self._serial_controller.device_identification[DID_CONSTRUCTOR],
            model=self._serial_controller.device_identification[DID_TYPE],
            name=DID_DEFAULT_NAME,
        )

    @property
    def is_on(self) -> bool:
        """Value of the sensor."""
        return self._serial_controller.is_connected()

class RelayState(BinarySensorEntity):
    """Serial connectivity to the Linky TIC serial interface."""

    # Generic properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_has_entity_name = True
    _attr_should_poll = False

    # Binary sensor properties
    #   https://developers.home-assistant.io/docs/core/entity/binary-sensor/#properties
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self, title: str, uniq_id: str | None, serial_reader: LinkyTICReader, relay_index: int
    ) -> None:
        """Initialize the SerialConnectivity binary sensor."""
        _LOGGER.debug(f"title: initializing binary sensor for relay {relay_index}")
        self._tag = "RELAIS"
        self._config_title = title
        self._config_uniq_id = uniq_id
        self._attr_unique_id = f"{DOMAIN}_{uniq_id}_{self._tag}_{relay_index}"
        self._attr_name = f"Relais {relay_index}"
        self._attr_icon = "mdi:electric-switch"
        self._serial_controller = serial_reader
        self._relay_index = relay_index - 1 # bit fields starts at index 0 for relay 1
        self._last_state = None

        # Relays always uses the realTime behavior: they cdo not change often,
        # and we want to be able to react resonably fast. So realTime is a better
        # option than polling.
        self._serial_controller.register_push_notif(
            self._tag, self.update_notification
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            default_manufacturer=DID_DEFAULT_MANUFACTURER,
            default_model=DID_DEFAULT_MODEL,
            default_name=DID_DEFAULT_NAME,
            identifiers={(DOMAIN, self._config_uniq_id)},
            manufacturer=self._serial_controller.device_identification[DID_CONSTRUCTOR],
            model=self._serial_controller.device_identification[DID_TYPE],
        )

    @property
    def is_on(self) -> bool:
        """Value of the sensor."""
        return self._last_state

    @callback
    def update(self):
        value, _ = self._serial_controller.get_values(self._tag)
        _LOGGER.debug(
            "%s: retrieved %s value from serial controller: %s",
            self._config_title,
            self._tag,
            repr(value),
        )
        value = int(value)
        # Handle entity availability
        if value is None:
            if self._attr_available and self._serial_controller.has_read_full_frame():
                _LOGGER.info(
                    "%s: marking the %s sensor as unavailable: a full frame has been read but RELAIS has not been found",
                    self._config_title,
                    self._attr_name
                )
                self._attr_available = False
        else:
            if not self._attr_available:
                _LOGGER.info(
                    "%s: marking the %s sensor as available now ! (was not previously)",
                    self._config_title,
                    self._attr_name,
                )
                self._attr_available = True

            # decode relay state
            state_bitfield = "{0:08b}".format(int(value))
            self._last_state = state_bitfield[self._relay_index] == "1"
            if self._last_state:
                self._attr_icon = "mdi:electric-switch-closed"
            else:
                self._attr_icon = "mdi:electric-switch"

            # Save value
            self._last_state = value

    def update_notification(self, realtime_option: bool) -> None:
        self.schedule_update_ha_state(force_refresh=True)
