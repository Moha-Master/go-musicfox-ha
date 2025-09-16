"""Media player platform for Go Musicfox HA."""
from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import GoMusicfoxAPI
from .const import DOMAIN, PLAY_MODE_MAP, PLAY_MODE_CODE_MAP

SUPPORT_GO_MUSICFOX = (
    MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Go Musicfox media player platform."""
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="go-musicfox-ha",
    )
    async_add_entities([GoMusicfoxMediaPlayer(hass, api, entry, device_info)])


class GoMusicfoxMediaPlayer(MediaPlayerEntity):
    """Representation of a Go Musicfox media player."""

    _attr_name = "Media Player"
    _attr_supported_features = SUPPORT_GO_MUSICFOX
    _attr_icon = "mdi:music"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, api: GoMusicfoxAPI, entry: ConfigEntry, device_info: DeviceInfo) -> None:
        """Initialize the media player."""
        self.hass = hass
        self._api = api
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_player"
        self._attr_device_info = device_info
        self._attr_state = MediaPlayerState.OFF # Default state

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
        """Handle status updates from the dispatcher."""
        status = self.hass.data[DOMAIN][self._entry_id].get("status", {})
        
        # When connection is lost, status becomes empty
        if not status:
            self._attr_state = MediaPlayerState.OFF
            self._attr_media_title = None
            self._attr_media_artist = None
            self.async_write_ha_state()
            return

        # When go-musicfox is running but no song is loaded
        if not status.get("song_title"):
            self._attr_state = MediaPlayerState.IDLE
        elif status.get("is_playing"):
            self._attr_state = MediaPlayerState.PLAYING
        else:
            self._attr_state = MediaPlayerState.PAUSED

        self._attr_media_title = status.get("song_title")
        self._attr_media_artist = status.get("artist")
        duration = status.get("song_duration")
        self._attr_media_duration = duration / 1_000_000_000 if duration else None
        position = status.get("playback_played")
        self._attr_media_position = position / 1_000_000_000 if position else None
        
        mode_code = status.get("play_mode")
        mode_str = PLAY_MODE_CODE_MAP.get(mode_code)
        self._attr_extra_state_attributes = {
            "play_mode": PLAY_MODE_MAP.get(mode_str),
            "is_logged_in": status.get("is_logged_in"),
            "lyric": (status.get("lyric") or "").split('\n')[0],
        }
        self.async_write_ha_state()

    async def async_media_play(self) -> None:
        await self._api.async_play()

    async def async_media_pause(self) -> None:
        await self._api.async_pause()

    async def async_media_next_track(self) -> None:
        await self._api.async_next()

    async def async_media_previous_track(self) -> None:
        await self._api.async_previous()