"""Sensor platform for Go Musicfox HA."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PLAY_MODE_CODE_MAP


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="go-musicfox",
    )

    sensors = [
        SongTitleSensor(hass, entry, device_info),
        ArtistSensor(hass, entry, device_info),
        PlayModeSensor(hass, entry, device_info),
        LyricSensor(hass, entry, device_info),
        LoggedInSensor(hass, entry, device_info),
        IsPlayingSensor(hass, entry, device_info),
        SongDurationSensor(hass, entry, device_info),
        PlaybackPlayedSensor(hass, entry, device_info),
        VolumeSensor(hass, entry, device_info),
        ProgressSensor(hass, entry, device_info),
    ]
    async_add_entities(sensors)


class BaseGoMusicfoxSensor(SensorEntity):
    """Base class for Go Musicfox sensors."""
    _attr_should_poll = False
    _attr_has_entity_name = True

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
    _attr_translation_key = "title"
    _attr_icon = "mdi:music-note"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_title"

    @property
    def native_value(self) -> str | None:
        return self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("song_title")


class ArtistSensor(BaseGoMusicfoxSensor):
    _attr_translation_key = "artist"
    _attr_icon = "mdi:account-music"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_artist"

    @property
    def native_value(self) -> str | None:
        return self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("artist")


class PlayModeSensor(BaseGoMusicfoxSensor):
    _attr_translation_key = "play_mode"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_play_mode"

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        mode_code = self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("play_mode")
        mode_str = PLAY_MODE_CODE_MAP.get(mode_code)
        if mode_str == "ordered":
            return "mdi:view-sequential"
        if mode_str == "list_loop":
            return "mdi:repeat"
        if mode_str == "single_loop":
            return "mdi:repeat-once"
        if mode_str == "list_random":
            return "mdi:shuffle"
        if mode_str == "inf_random":
            return "mdi:shuffle-variant"
        if mode_str == "intelligent":
            return "mdi:heart"
        return "mdi:playlist-music"

    @property
    def native_value(self) -> str | None:
        status = self.hass.data[DOMAIN][self._entry_id].get("status", {})
        mode_code = status.get("play_mode")
        return PLAY_MODE_CODE_MAP.get(mode_code)


class LyricSensor(BaseGoMusicfoxSensor):
    _attr_translation_key = "lyric"
    _attr_icon = "mdi:text-long"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_lyric"

    @property
    def native_value(self) -> str | None:
        full_lyric = self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("lyric", "")
        return full_lyric.split('\n')[0] if full_lyric else None


class LoggedInSensor(BaseGoMusicfoxSensor):
    _attr_translation_key = "is_logged_in"
    _attr_icon = "mdi:login"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_is_logged_in"

    @property
    def native_value(self) -> bool | None:
        return self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("is_logged_in")


class IsPlayingSensor(BaseGoMusicfoxSensor):
    _attr_translation_key = "is_playing"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_is_playing"

    @property
    def icon(self) -> str:
        """Return dynamic icon based on playing state."""
        is_playing = self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("is_playing")
        if is_playing:
            return "mdi:play-circle"
        return "mdi:pause-box"

    @property
    def native_value(self) -> bool | None:
        return self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("is_playing")


class SongDurationSensor(BaseGoMusicfoxSensor):
    """Sensor for song duration."""
    _attr_translation_key = "duration"
    _attr_icon = "mdi:timer"
    _attr_device_class = "duration"
    _attr_native_unit_of_measurement = "s"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_duration"

    @property
    def native_value(self) -> float | None:
        duration = self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("song_duration")
        if duration:
            return round(duration / 1_000_000_000, 2)
        return None

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the state attributes."""
        duration = self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("song_duration")
        if duration:
            seconds = duration / 1_000_000_000
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return {
                "duration_formatted": f"{minutes:02d}:{seconds:02d}"
            }
        return None


class PlaybackPlayedSensor(BaseGoMusicfoxSensor):
    """Sensor for playback played time."""
    _attr_translation_key = "playback_played"
    _attr_icon = "mdi:progress-clock"
    _attr_device_class = "duration"
    _attr_native_unit_of_measurement = "s"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_playback_played"

    @property
    def native_value(self) -> float | None:
        played = self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("playback_played")
        if played:
            return round(played / 1_000_000_000, 2)
        return None

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the state attributes."""
        played = self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("playback_played")
        if played:
            seconds = played / 1_000_000_000
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return {
                "played_formatted": f"{minutes:02d}:{seconds:02d}"
            }
        return None


class VolumeSensor(BaseGoMusicfoxSensor):
    """Sensor for volume."""
    _attr_translation_key = "volume"
    _attr_icon = "mdi:volume-high"
    _attr_native_unit_of_measurement = "%"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_volume"

    @property
    def native_value(self) -> int | None:
        return self.hass.data[DOMAIN][self._entry_id].get("status", {}).get("volume")


class ProgressSensor(BaseGoMusicfoxSensor):
    """Sensor for playback progress percentage."""
    _attr_translation_key = "progress"
    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo
    ) -> None:
        super().__init__(hass, entry, device_info)
        self._attr_unique_id = f"{entry.entry_id}_musicfox_progress"

    @property
    def native_value(self) -> float | None:
        status = self.hass.data[DOMAIN][self._entry_id].get("status", {})
        played = status.get("playback_played")
        duration = status.get("song_duration")
        
        if played is not None and duration is not None and duration > 0:
            return round((played / duration) * 100, 2)
        return None
