import discord

CYBERPUNK_COLOR = discord.Color.from_rgb(255, 0, 255)


def cyberpunk_embed(title: str | None = None,
                    description: str | None = None,
                    *,
                    color: discord.Color = CYBERPUNK_COLOR) -> discord.Embed:
    """Return an embed using the default cyberpunk style."""
    return discord.Embed(title=title, description=description, color=color)
