"""Energy sensors for Linky (LiXee-TIC-DIN) integration"""
from __future__ import annotations
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Linky (LiXee-TIC-DIN) platform."""

    # hass.bus.async_listen_once(
    #     EVENT_HOMEASSISTANT_STOP, sensor.stop_serial_read)
    _LOGGER.warning("lixee adding sensors")
    async_add_entities([BASE()], True)


class BASE(SensorEntity):
    """Index option Base sensor"""

    # Generic properties
    #   https://developers.home-assistant.io/docs/core/entity#generic-properties
    _attr_icon = "mdi:counter"
    _attr_name = "Index option Base"
    _attr_should_poll = False
    _attr_unique_id = "base"

    # Lifecycle hooks
    #   https://developers.home-assistant.io/docs/core/entity#lifecycle-hooks
    # async def async_added_to_hass(self):
    #     """Called when an entity has their entity_id and hass object assigned,
    #     before it is written to the state machine for the first time."""
    #     pass

    # async def async_will_remove_from_hass(self):
    #     """Called when an entity is about to be removed from Home Assistant."""
    #     pass

    # Sensor Entity Properties
    #   https://developers.home-assistant.io/docs/core/entity/sensor/#properties
    _attr_device_class = SensorDeviceClass.ENERGY
    # _attr_last_reset = None
    _attr_native_value = 42
    _attr_native_unit_of_measurement = "Wh"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self):
        _LOGGER.debug("initing BASE sensor")