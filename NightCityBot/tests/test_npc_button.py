from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock
import config


async def run(suite, ctx) -> List[str]:
    """Send the NPC button and click it."""
    logs: List[str] = []
    cog = suite.bot.get_cog("RoleButtons")
    if not cog:
        logs.append("❌ RoleButtons cog not loaded")
        return logs

    ctx.send = AsyncMock()
    await cog.npc_button.callback(cog, ctx)
    suite.assert_send(logs, ctx.send, "ctx.send")

    view = ctx.send.call_args.kwargs.get("view")
    if not view:
        logs.append("❌ NPC button view not sent")
        return logs

    member = MagicMock(spec=discord.Member)
    member.roles = []
    member.add_roles = AsyncMock()
    guild = MagicMock()
    guild.get_role.return_value = discord.Object(id=config.NPC_ROLE_ID)

    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = member
    interaction.guild = guild
    interaction.response.send_message = AsyncMock()

    button = view.children[0]
    await button.callback(interaction)

    suite.assert_send(logs, member.add_roles, "add_roles")
    suite.assert_send(logs, interaction.response.send_message, "send_message")
    return logs

