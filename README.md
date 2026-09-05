# Oyaki Senpai

A developer-only Discord bot for server-dev work: channel management, role +
per-channel permission management, quick embeds, and emoji stealing.

Every single command only works for **your** Discord account
(`978988982375415808`). Anyone else typing a command gets silently ignored.

## Commands

Prefixes: `.` `!` `?` (edit `PREFIXES` in `config.py` to change — there's no
in-chat way to change it, on purpose).

**Channels**
- `channel create <text|voice|category> <name> [category]`
- `channel delete <#channel>`
- `channel rename <#channel> <new name>`
- `channel topic <#channel> <text>`
- `channel slowmode <#channel> <seconds>`
- `channel nsfw <#channel> <true|false>`
- `channel move <#channel> <category>`
- `channel lock [#channel]` / `channel unlock [#channel]`
- `channel list`

**Roles & permissions**
- `role create <name> [hex_color] [hoist] [mentionable]`
- `role delete <@role>`
- `role rename <@role> <new name>`
- `role color <@role> <hex>`
- `role hoist <@role> <true|false>`
- `role mentionable <@role> <true|false>`
- `role perm <#channel> <@role> <permission> <allow|deny|neutral>`
  (permission = any discord.py permission flag, e.g. `send_messages`,
  `view_channel`, `manage_messages`, `connect`, `speak`)
- `role perms <#channel> <@role>` — view current overwrites

**Embeds**
- `embed <#channel> <description> [image url]` — or attach an image to the
  command message instead of a URL

**Emoji stealing**
- `steal <:emoji1:> <:emoji2:>` — paste emoji(s) straight from another server
- `steal` (as a reply to a message with emojis in it) — steals everything in
  that message

## Setup

1. **Create the bot application**: https://discord.com/developers/applications
   → New Application → Bot tab → Reset Token (save it) → enable
   **Message Content Intent** and **Server Members Intent**.
2. **Invite it** with the OAuth2 URL Generator: scope `bot`, and permissions
   at least: Manage Channels, Manage Roles, Manage Emojis and Stickers,
   Send Messages, Embed Links, Read Message History.
3. **Push this folder to a GitHub repo.**
4. In the repo, go to **Settings → Secrets and variables → Actions → New
   repository secret**, name it `APP_TOKEN`, paste the bot token.
5. Go to the **Actions** tab and enable workflows if prompted. The
   `Oyaki Senpai` workflow will run automatically on push, and re-trigger
   itself every ~6 hours to stay online continuously (see below).

## About hosting: why there's no Uptime Robot step

You asked to host with just GitHub + Uptime Robot and no extra bridge. In
practice those two don't actually connect to each other for this kind of
bot: Uptime Robot works by pinging a public HTTP URL, and a GitHub Actions
job has no public URL for it to ping — it's just a script running on a
temporary runner, with no inbound networking at all. Wiring in a small web
server for Uptime Robot to hit would give you a URL that responds, but it
wouldn't actually keep GitHub Actions running any longer, so it would only
add a moving part without doing anything.

What actually keeps a GitHub-Actions-only bot online is in
`.github/workflows/bot.yml`: every job is capped at 6 hours, so the
workflow sets `timeout-minutes: 350` (so it exits cleanly just before that
cutoff) and a `schedule: cron` that starts a fresh run every 5h50m. That
overlap is what gives you continuous uptime using nothing but GitHub itself
— no Repl, no Render, no Uptime Robot needed.

If you'd still like Uptime Robot doing *something* useful (e.g. as a
redundant "kick it back on" trigger), the real way to wire it up is: add
`repository_dispatch` as a trigger in the workflow, then set an Uptime
Robot monitor (needs a paid plan for custom headers) to POST to
`https://api.github.com/repos/<you>/<repo>/dispatches` with an
`Authorization: token <a GitHub PAT>` header and body
`{"event_type": "ping"}` every few minutes. That's optional — the
cron schedule above already keeps the bot running without it.

## Files

```
main.py                       bot entrypoint
config.py                     developer ID + prefixes (edit here)
cogs/channels.py               channel commands
cogs/roles.py                  role + permission commands
cogs/embeds.py                 embed command
cogs/emojis.py                 emoji steal command
requirements.txt
.github/workflows/bot.yml      keeps the bot running via GitHub Actions
```
