import os
import discord
from discord.ext import commands, tasks
from discord import AllowedMentions
import aiosqlite
from dotenv import load_dotenv
from datetime import datetime, timedelta

# ------------------------------
# LOAD ENV VARIABLES
# ------------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set!")

DB_FILE = "timers.db"

# ------------------------------
# INTENTS & BOT SETUP
# ------------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    allowed_mentions=AllowedMentions(roles=True)
)

# ------------------------------
# DATABASE INITIALIZATION
# ------------------------------
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS timers (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            role_id INTEGER
        )
        """)
        await db.commit()

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
async def get_server_config(guild_id):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT channel_id, role_id FROM timers WHERE guild_id=?", (guild_id,))
        row = await cursor.fetchone()
        if row:
            return row  # (channel_id, role_id)
        return None

async def save_server_config(guild_id, channel_id, role_id):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        INSERT INTO timers (guild_id, channel_id, role_id)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET channel_id=excluded.channel_id, role_id=excluded.role_id
        """, (guild_id, channel_id, role_id))
        await db.commit()

# ------------------------------
# TIMER LOOP
# ------------------------------
@tasks.loop(hours=2)
async def ping_loop():
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT guild_id, channel_id, role_id FROM timers")
        rows = await cursor.fetchall()

    for guild_id, channel_id, role_id in rows:
        guild = bot.get_guild(guild_id)
        if not guild:
            continue

        channel = guild.get_channel(channel_id)
        if not channel:
            try:
                channel = await bot.fetch_channel(channel_id)
            except:
                continue

        try:
            await channel.send(f"<@&{role_id}> World Boss in 10 minutes ⏰!")
        except Exception as e:
            print(f"[ERROR] Sending ping in guild {guild_id}: {e}")

# ------------------------------
# COMMANDS
# ------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def set_timer(ctx, channel: discord.TextChannel, role: discord.Role):
    """Set the timer channel and ping role for your server"""
    await save_server_config(ctx.guild.id, channel.id, role.id)
    await ctx.send(f"✅ Timer set! Channel: {channel.mention}, Role: {role.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def start(ctx):
    """Start the world boss timer loop manually"""
    if not ping_loop.is_running():
        ping_loop.start()
    await ctx.send("✅ Timer loop started!")

@bot.command()
@commands.has_permissions(administrator=True)
async def stop(ctx):
    """Stop the world boss timer loop manually"""
    if ping_loop.is_running():
        ping_loop.stop()
        await ctx.send("⏹ Timer loop stopped.")
    else:
        await ctx.send("⛔ Timer loop isn't running.")

# ------------------------------
# READY EVENT
# ------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await init_db()
    if not ping_loop.is_running():
        ping_loop.start()
        print("Timer loop started")

# ------------------------------
bot.run(TOKEN)
