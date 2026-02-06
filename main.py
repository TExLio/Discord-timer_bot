# main.py
import os
import discord
from discord.ext import commands, tasks
from discord import AllowedMentions

# ===== LOAD TOKEN (Railway uses environment variables) =====
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise RuntimeError("DISCORD_TOKEN is not set in Railway Variables")

# ===== CONFIG (PUT REAL IDS HERE, NO QUOTES) =====
CHANNEL_ID = 123456789012345678  # <-- your channel ID
WORLD_BOSS_ROLE_ID = 123456789012345678  # <-- your role ID

# ===== INTENTS =====
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    allowed_mentions=AllowedMentions(roles=True)
)

# ===== TIMER LOOP =====
@tasks.loop(hours=2)
async def ping_loop():
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(CHANNEL_ID)

        await channel.send(
            f"<@&{WORLD_BOSS_ROLE_ID}> World Boss in 10 minutes ⏰!"
        )
    except Exception as e:
        print(f"[ERROR] ping_loop: {e}")

# ===== EVENTS =====
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    if not ping_loop.is_running():
        ping_loop.start()
        print("Timer loop started")

# ===== COMMANDS =====
@bot.command()
async def start(ctx):
    if ping_loop.is_running():
        await ctx.send("⏳ Timer is already running.")
        return

    ping_loop.start()
    await ctx.send("✅ Timer started!")

@bot.command()
async def stop(ctx):
    if ping_loop.is_running():
        ping_loop.stop()
        await ctx.send("⏹ Timer stopped.")
    else:
        await ctx.send("⛔ Timer isn't running.")

# ===== RUN BOT =====
bot.run(TOKEN)
