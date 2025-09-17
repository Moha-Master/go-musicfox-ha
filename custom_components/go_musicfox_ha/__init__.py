"""The Go Musicfox HA integration."""
from __future__ import annotations

import asyncio
import json
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN
from .api import GoMusicfoxAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Go Musicfox HA from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]
    sse_url = f"http://{host}:{port}/api/v1/events"
    api = GoMusicfoxAPI(host, port)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "status": {}, # Initialize status
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def sse_listen(event=None):
        """A robust, low-level SSE client implementation."""
        reconnect_delay = 5
        timeout = aiohttp.ClientTimeout(total=None, connect=5, sock_connect=5)

        while True:
            try:
                _LOGGER.info("SSE: Attempting to connect to: %s", sse_url)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(sse_url) as resp:
                        if resp.status == 200:
                            _LOGGER.info("SSE: Connection established.")
                            async for line in resp.content:
                                line = line.decode('utf-8').strip()
                                if line.startswith("data:"):
                                    data_str = line[len("data:"):].strip()
                                    try:
                                        status = json.loads(data_str)
                                        hass.data[DOMAIN][entry.entry_id]["status"] = status
                                        async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}_update")
                                    except json.JSONDecodeError:
                                        _LOGGER.warning("SSE: Invalid JSON received: %s", data_str)
                        else:
                            _LOGGER.error("SSE: Connection failed with status: %d", resp.status)

            except asyncio.TimeoutError:
                _LOGGER.warning("SSE: Connection timed out. Reconnecting in %d seconds.", reconnect_delay)
            except aiohttp.ClientError as e:
                _LOGGER.warning("SSE: Connection failed (ClientError): %s. Reconnecting in %d seconds.", e, reconnect_delay)
            except Exception as e:
                _LOGGER.error("SSE: Unexpected error: %s. Reconnecting in %d seconds.", e, reconnect_delay)
            finally:
                if entry.entry_id in hass.data[DOMAIN]:
                    hass.data[DOMAIN][entry.entry_id]["status"] = {}
                    async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}_update")
                _LOGGER.info("SSE: Connection closed. Reconnecting in %d seconds.", reconnect_delay)
                await asyncio.sleep(reconnect_delay)

    def start_sse_task(event=None):
        """Thread-safe way to start the SSE listener task."""
        sse_task = hass.loop.call_soon_threadsafe(
            hass.async_create_task, sse_listen()
        )
        hass.data[DOMAIN][entry.entry_id]["sse_task"] = sse_task
        # Note: We can't easily cancel a task started this way on unload.
        # This is a known complexity with this pattern.

    if hass.state is CoreState.running:
        start_sse_task()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_sse_task)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Proper cancellation of tasks started with call_soon_threadsafe is complex
    # and might require a more advanced setup if unload is critical.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        if entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok