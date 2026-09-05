import os
import re
import asyncio

import aiohttp
import discord
from discord.ext import commands

# ─────────────────────────────────────────────
# CONFIG — edit these two values directly, no in-chat way to change them
# ─────────────────────────────────────────────
DEVELOPER_ID = 978988982375415808
PREFIXES = [".", "!", "?"]

VALID_PERMS = set(discord.Permissions.VALID_FLAGS.keys())
EMOJI_RE = re.compile(r"<(a?):(\w+):(\d+)>")
IMAGE_URL_RE = re.compile(r"(https?://\S+\.(?:png|jpe?g|gif|webp))(\?\S*)?\s*$", re.IGNORECASE)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.emojis_and_stickers = True

bot = commands.Bot(command_prefix=PREFIXES, intents=intents, help_command=commands.DefaultHelpCommand())


@bot.check
async def developer_only(ctx: commands.Context) -> bool:
    """Global check — every command only works for the developer."""
    return ctx.author.id == DEVELOPER_ID


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print(f"Prefixes: {', '.join(PREFIXES)}")
    print(f"Developer-only ID: {DEVELOPER_ID}")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, (commands.CheckFailure, commands.CommandNotFound)):
        return  # non-developer or typo — ignore silently
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: `{error.param.name}`")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"⚠️ Bad argument: {error}")
        return
    if isinstance(error, discord.Forbidden):
        await ctx.send("⚠️ I don't have permission to do that (check my role position/permissions).")
        return
    print(f"Unhandled error in command '{ctx.command}': {error!r}")
    await ctx.send(f"⚠️ Error: `{error}`")


# ═════════════════════════════════════════════
# CHANNELS
# ═════════════════════════════════════════════
@bot.group(invoke_without_command=True)
async def channel(ctx: commands.Context):
    await ctx.send_help(ctx.command)


@channel.command(name="create")
async def channel_create(ctx, ch_type: str, name: str, category: discord.CategoryChannel = None):
    """.channel create <text|voice|category> <name> [category]"""
    ch_type = ch_type.lower()
    if ch_type in ("text", "txt"):
        new_ch = await ctx.guild.create_text_channel(name, category=category)
    elif ch_type in ("voice", "vc"):
        new_ch = await ctx.guild.create_voice_channel(name, category=category)
    elif ch_type in ("category", "cat"):
        new_ch = await ctx.guild.create_category(name)
    else:
        await ctx.send("⚠️ Type must be `text`, `voice`, or `category`.")
        return
    await ctx.send(f"✅ Created {getattr(new_ch, 'mention', f'`{new_ch.name}`')}")


@channel.command(name="delete")
async def channel_delete(ctx, channel: discord.abc.GuildChannel):
    """.channel delete <#channel>"""
    name = channel.name
    await channel.delete(reason=f"Deleted via bot by {ctx.author}")
    await ctx.send(f"🗑️ Deleted `{name}`")


@channel.command(name="rename")
async def channel_rename(ctx, channel: discord.abc.GuildChannel, *, new_name: str):
    """.channel rename <#channel> <new name>"""
    old = channel.name
    await channel.edit(name=new_name)
    await ctx.send(f"✏️ Renamed `{old}` → `{new_name}`")


@channel.command(name="topic")
async def channel_topic(ctx, channel: discord.TextChannel, *, text: str):
    """.channel topic <#channel> <new topic>"""
    await channel.edit(topic=text)
    await ctx.send(f"✅ Updated topic for {channel.mention}")


@channel.command(name="slowmode")
async def channel_slowmode(ctx, channel: discord.TextChannel, seconds: int):
    """.channel slowmode <#channel> <seconds>"""
    await channel.edit(slowmode_delay=seconds)
    await ctx.send(f"🐌 Slowmode for {channel.mention} set to {seconds}s")


@channel.command(name="nsfw")
async def channel_nsfw(ctx, channel: discord.TextChannel, value: bool):
    """.channel nsfw <#channel> <true|false>"""
    await channel.edit(nsfw=value)
    await ctx.send(f"✅ NSFW for {channel.mention} set to `{value}`")


@channel.command(name="move")
async def channel_move(ctx, channel: discord.abc.GuildChannel, category: discord.CategoryChannel):
    """.channel move <#channel> <category>"""
    await channel.edit(category=category)
    await ctx.send(f"📁 Moved `{channel.name}` into `{category.name}`")


@channel.command(name="lock")
async def channel_lock(ctx, channel: discord.TextChannel = None):
    """.channel lock [#channel] — denies @everyone Send Messages"""
    channel = channel or ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(f"🔒 Locked {channel.mention}")


@channel.command(name="unlock")
async def channel_unlock(ctx, channel: discord.TextChannel = None):
    """.channel unlock [#channel]"""
    channel = channel or ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = None
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(f"🔓 Unlocked {channel.mention}")


@channel.command(name="list")
async def channel_list(ctx: commands.Context):
    """.channel list — shows every channel grouped by category"""
    categories: dict[str, list[str]] = {}
    for ch in ctx.guild.channels:
        if isinstance(ch, discord.CategoryChannel):
            continue
        cat_name = ch.category.name if ch.category else "No Category"
        categories.setdefault(cat_name, []).append(ch.name)

    lines = [f"**{cat}**: " + ", ".join(chs) for cat, chs in categories.items()]
    embed = discord.Embed(
        title=f"Channels in {ctx.guild.name}",
        description="\n".join(lines)[:4000] or "No channels.",
        colour=discord.Colour.blurple(),
    )
    await ctx.send(embed=embed)


# ═════════════════════════════════════════════
# ROLES & PERMISSIONS
# ═════════════════════════════════════════════
@bot.group(invoke_without_command=True)
async def role(ctx: commands.Context):
    await ctx.send_help(ctx.command)


@role.command(name="create")
async def role_create(ctx, name: str, color: str = None, hoist: bool = False, mentionable: bool = False):
    """.role create <name> [hex_color] [hoist] [mentionable]"""
    colour = discord.Colour(int(color.lstrip("#"), 16)) if color else discord.Colour.default()
    new_role = await ctx.guild.create_role(name=name, colour=colour, hoist=hoist, mentionable=mentionable)
    await ctx.send(f"✅ Created role {new_role.mention}")


@role.command(name="delete")
async def role_delete(ctx, role: discord.Role):
    """.role delete <@role>"""
    name = role.name
    await role.delete()
    await ctx.send(f"🗑️ Deleted role `{name}`")


@role.command(name="rename")
async def role_rename(ctx, role: discord.Role, *, new_name: str):
    """.role rename <@role> <new name>"""
    await role.edit(name=new_name)
    await ctx.send(f"✏️ Renamed role to `{new_name}`")


@role.command(name="color")
async def role_color(ctx, role: discord.Role, hex_color: str):
    """.role color <@role> <hex>"""
    await role.edit(colour=discord.Colour(int(hex_color.lstrip("#"), 16)))
    await ctx.send(f"🎨 Updated color for {role.mention}")


@role.command(name="hoist")
async def role_hoist(ctx, role: discord.Role, value: bool):
    """.role hoist <@role> <true|false>"""
    await role.edit(hoist=value)
    await ctx.send(f"✅ Hoist for {role.mention} set to `{value}`")


@role.command(name="mentionable")
async def role_mentionable(ctx, role: discord.Role, value: bool):
    """.role mentionable <@role> <true|false>"""
    await role.edit(mentionable=value)
    await ctx.send(f"✅ Mentionable for {role.mention} set to `{value}`")


@role.command(name="perm")
async def role_perm(ctx, channel: discord.abc.GuildChannel, role: discord.Role, permission: str, state: str):
    """.role perm <#channel> <@role> <permission> <allow|deny|neutral>
    Example: .role perm #general @Moderators manage_messages allow
    """
    permission = permission.lower()
    if permission not in VALID_PERMS:
        await ctx.send(
            f"⚠️ Unknown permission `{permission}`. "
            f"Examples: `send_messages`, `view_channel`, `manage_messages`, `connect`, `speak`."
        )
        return

    state = state.lower()
    overwrite = channel.overwrites_for(role)
    if state == "allow":
        setattr(overwrite, permission, True)
    elif state == "deny":
        setattr(overwrite, permission, False)
    elif state == "neutral":
        setattr(overwrite, permission, None)
    else:
        await ctx.send("⚠️ State must be `allow`, `deny`, or `neutral`.")
        return

    await channel.set_permissions(role, overwrite=overwrite)
    await ctx.send(f"✅ Set `{permission}` → `{state}` for {role.mention} in {getattr(channel, 'mention', channel.name)}")


@role.command(name="perms")
async def role_perms(ctx, channel: discord.abc.GuildChannel, role: discord.Role):
    """.role perms <#channel> <@role> — view current overwrites"""
    overwrite = channel.overwrites_for(role)
    pairs = [f"{name}: {val}" for name, val in overwrite if val is not None]
    desc = "\n".join(pairs) if pairs else "No overwrites set."
    embed = discord.Embed(
        title=f"Overwrites for {role.name} in #{channel.name}",
        description=desc,
        colour=discord.Colour.blurple(),
    )
    await ctx.send(embed=embed)


# ═════════════════════════════════════════════
# EMBEDS
# ═════════════════════════════════════════════
@bot.command(name="embed")
async def embed_cmd(ctx: commands.Context, channel: discord.TextChannel, *, description: str):
    """.embed <#channel> <description> [image url]
    You can also just attach an image to the command message instead of a URL.
    """
    image_url = None
    stripped = description.strip()
    match = IMAGE_URL_RE.search(stripped)
    if match:
        image_url = match.group(1)
        description = stripped[: match.start()].strip()
    elif ctx.message.attachments:
        image_url = ctx.message.attachments[0].url

    embed = discord.Embed(description=description, colour=discord.Colour.blurple())
    if image_url:
        embed.set_image(url=image_url)

    await channel.send(embed=embed)
    try:
        await ctx.message.add_reaction("✅")
    except discord.HTTPException:
        pass


# ═════════════════════════════════════════════
# EMOJI STEALING
# ═════════════════════════════════════════════
async def _steal_one(ctx: commands.Context, session: aiohttp.ClientSession, animated: bool, name: str, emoji_id: str):
    ext = "gif" if animated else "png"
    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"
    async with session.get(url) as resp:
        if resp.status != 200:
            await ctx.send(f"⚠️ Couldn't download emoji `{name}` (HTTP {resp.status})")
            return None
        data = await resp.read()
    try:
        return await ctx.guild.create_custom_emoji(name=name, image=data, reason=f"Stolen via bot by {ctx.author}")
    except discord.HTTPException as e:
        await ctx.send(f"⚠️ Failed to add `{name}`: {e}")
        return None


@bot.command(name="steal")
async def steal(ctx: commands.Context, *, emojis: str = None):
    """.steal <:emoji1:> <:emoji2:> ... — or reply to a message containing emojis"""
    targets = []
    if emojis:
        targets.extend(EMOJI_RE.findall(emojis))

    if ctx.message.reference:
        ref_msg = ctx.message.reference.resolved
        if ref_msg is None:
            try:
                ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                ref_msg = None
        if ref_msg:
            targets.extend(EMOJI_RE.findall(ref_msg.content))

    if not targets:
        await ctx.send("⚠️ No custom emojis found. Paste the emoji(s) in the command, or reply to a message that contains them.")
        return

    async with aiohttp.ClientSession() as session:
        added = []
        for animated_flag, name, emoji_id in targets:
            result = await _steal_one(ctx, session, bool(animated_flag), name, emoji_id)
            if result:
                added.append(str(result))

    if added:
        await ctx.send(f"✅ Added {len(added)} emoji(s): " + " ".join(added))


# ═════════════════════════════════════════════
# ENTRYPOINT
# ═════════════════════════════════════════════
async def main():
    async with bot:
        token = os.environ.get("APP_TOKEN")
        if not token:
            raise RuntimeError(
                "APP_TOKEN environment variable is not set. "
                "In GitHub, set it under Settings → Secrets and variables → Actions."
            )
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
