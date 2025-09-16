"""Button platform for Go Musicfox HA."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .api import GoMusicfoxAPI

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="go-musicfox-ha",
    )

    buttons = [
        IntelligentModeButton(api, entry.entry_id, device_info),
        NextModeButton(api, entry.entry_id, device_info),
    ]
    async_add_entities(buttons)

class GoMusicfoxButton(ButtonEntity):
    """Base class for Go Musicfox buttons."""
    _attr_should_poll = False

    def __init__(self, api: GoMusicfoxAPI, entry_id: str, device_info: DeviceInfo) -> None:
        """Initialize the button."""
        self._api = api
        self._attr_device_info = device_info

class IntelligentModeButton(GoMusicfoxButton):
    """Representation of an intelligent mode button."""

    _attr_name = "Activate Intelligent Mode"
    _attr_icon = "mdi:heart-music"

    def __init__(self, api: GoMusicfoxAPI, entry_id: str, device_info: DeviceInfo) -> None:
        """Initialize the button."""
        super().__init__(api, entry_id, device_info)
        self._attr_unique_id = f"{entry_id}_intelligent_mode"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._api.async_activate_intelligent_mode()

class NextModeButton(GoMusicfoxButton):
    """Representation of a next mode button."""

    _attr_name = "Next Play Mode"
    _attr_icon = "mdi:shuffle-variant"

    def __init__(self, api: GoMusicfoxAPI, entry_id: str, device_info: DeviceInfo) -> None:
        """Initialize the button."""
        super().__init__(api, entry_id, device_info)
        self._attr_unique_id = f"{entry_id}_next_mode"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._api.async_next_play_mode()