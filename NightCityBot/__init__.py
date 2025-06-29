"""NightCityBot package setup."""

from __future__ import annotations

import discord

# Original send method reference for patching in tests
orig_send = discord.abc.Messageable.send

async def _chunked_send(self: discord.abc.Messageable, content: str | None = None, **kwargs):
    """Send long messages in 1900-character chunks."""
    if isinstance(content, str) and len(content) > 1900 and not kwargs.get("embed") and not kwargs.get("embeds"):
        for chunk in (content[i : i + 1900] for i in range(0, len(content), 1900)):
            await orig_send(self, chunk, **kwargs)
        return
    await orig_send(self, content=content, **kwargs)

# Patch globally
discord.abc.Messageable.send = _chunked_send

__all__ = ["orig_send"]
