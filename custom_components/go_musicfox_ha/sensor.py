"""Sensor platform for Go Musicfox HA."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PLAY_MODE_MAP, PLAY_MODE_CODE_MAP


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="go-musicfox-ha",
    )

    sensors = [
        SongTitleSensor(hass, entry, device_info),
        ArtistSensor(hass, entry, device_info),
        PlayModeSensor(hass, entry, device_info),
        LyricSensor(hass, entry, device_info),
        LoggedInSensor(hass, entry, device_info),
    ]
    async_add_entities(sensors)


class BaseGoMusicfoxSensor(SensorEntity):
    """Base class for Go Musicfox sensors."""
    _attr_should_poll = False

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry_id = entry.entry_id
        self._attr_device_info = device_info

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
        self.async_write_ha_state()


class SongTitleSensor(BaseGoMusicfoxSensor):
    _attr_name = "Song Title"
    _attr_icon = "mdi:music-note"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_song_title"

    @property
    def native_value(self) -> str | None:
        return self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("song_title")


class ArtistSensor(BaseGoMusicfoxSensor):
    _attr_name = "Artist"
    _attr_icon = "mdi:account-music"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_artist"

    @property
    def native_value(self) -> str | None:
        return self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("artist")


class PlayModeSensor(BaseGoMusicfoxSensor):
    _attr_name = "Play Mode Sensor"
    _attr_icon = "mdi:playlist-music"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_play_mode_sensor"

    @property
    def native_value(self) -> str | None:
        status = self.hass.data[DOMAIN][self._entry_id].get("status", {})
        mode_code = status.get("play_mode")
        mode_str = PLAY_MODE_CODE_MAP.get(mode_code)
        return PLAY_MODE_MAP.get(mode_str)


class LyricSensor(BaseGoMusicfoxSensor):
    _attr_name = "Lyric"
    _attr_icon = "mdi:text-long"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_lyric"

    @property
    def native_value(self) -> str | None:
        full_lyric = self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("lyric", "")
        return full_lyric.split('\n')[0] if full_lyric else None


class LoggedInSensor(BaseGoMusicfoxSensor):
    _attr_name = "Is Logged In"
    _attr_icon = "mdi:login-variant"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_is_logged_in"

    @property
    def native_value(self) -> bool | None:
        return self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("is_logged_in")
