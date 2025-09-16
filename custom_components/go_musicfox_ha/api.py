"""API for Go Musicfox."""
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class GoMusicfoxAPI:
    """A simple API wrapper for Go Musicfox."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the API."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api/v1"

    async def _send_command(self, command: str, args: list | None = None) -> None:
        """Send a command to the Go Musicfox API."""
        url = f"{self.base_url}/command"
        payload = {"command": command, "args": args or []}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error(
                            "Error sending command '%s': %s",
                            command,
                            await response.text(),
                        )
                    response.raise_for_status()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with Go Musicfox: %s", err)

    async def async_set_play_mode(self, mode: str) -> None:
        """Set the play mode."""
        await self._send_command("set_play_mode", [mode])

    async def async_play(self) -> None:
        """Send play command."""
        await self._send_command("play")

    async def async_pause(self) -> None:
        """Send pause command."""
        await self._send_command("pause")

    async def async_next(self) -> None:
        """Send next command."""
        await self._send_command("next")

    async def async_previous(self) -> None:
        """Send previous command."""
        await self._send_command("previous")

    async def async_next_play_mode(self) -> None:
        """Send next_play_mode command."""
        await self._send_command("next_play_mode")

    async def async_activate_intelligent_mode(self) -> None:
        """Send activate_intelligent_mode command."""
        await self._send_command("activate_intelligent_mode")

    async def async_get_status(self) -> dict:
        """Get the current player status."""
        url = f"{self.base_url}/status"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with Go Musicfox: %s", err)
            return {}