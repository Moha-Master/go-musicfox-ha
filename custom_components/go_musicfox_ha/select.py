"""Select platform for Go Musicfox HA."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PLAY_MODE_MAP, PLAY_MODE_CODE_MAP
from .api import GoMusicfoxAPI

SELECTABLE_PLAY_MODES = {k: v for k, v in PLAY_MODE_MAP.items() if k != "intelligent"}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="go-musicfox-ha",
    )
    
    select_entity = PlayModeSelect(hass, api, entry, device_info)
    async_add_entities([select_entity])

class PlayModeSelect(SelectEntity):
    """Representation of a play mode select entity."""

    _attr_name = "Play Mode"
    _attr_icon = "mdi:playlist-music"
    _attr_options = list(SELECTABLE_PLAY_MODES.values())
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, api: GoMusicfoxAPI, entry: ConfigEntry, device_info: DeviceInfo) -> None:
        """Initialize the select entity."""
        self.hass = hass
        self._api = api
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_play_mode"
        self._attr_device_info = device_info
        self._attr_current_option = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self._entry_id}_update",
                self._handle_status_update,
            )
        )

    @callback
    def _handle_status_update(self) -> None:
        """Handle status updates."""
        status = self.hass.data[DOMAIN][self._entry_id].get("status", {})
        mode_code = status.get("play_mode")
        mode_str = PLAY_MODE_CODE_MAP.get(mode_code)
        self._attr_current_option = PLAY_MODE_MAP.get(mode_str)
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        backend_mode = next(
            (k for k, v in SELECTABLE_PLAY_MODES.items() if v == option), None
        )
        if backend_mode:
            await self._api.async_set_play_mode(backend_mode)