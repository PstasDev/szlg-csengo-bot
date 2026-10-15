import discord
from discord import app_commands
from discord.ext import commands
import dotenv
dotenv.load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# A cVLC stream URL-je
STREAM_URL = dotenv.get_key(dotenv.find_dotenv(), "STREAM_URL")

@bot.event
async def on_ready():
    # Szinkronizáljuk a slash parancsokat a Discord felé
    try:
        synced = await bot.tree.sync()
        print(f"Sikeresen szinkronizálva {len(synced)} Slash parancs.")
    except Exception as e:
        print(f"Hiba a szinkronizáció során: {e}")
    print(f"Bot bejelentkezve mint: {bot.user.name}")

@bot.tree.command(name="csatlakozz", description="A bot belép a hangcsatornába és elindítja a csengő streamet")
async def csatlakozz(interaction: discord.Interaction):
    # Ellenőrizzük, hogy a parancsot kiadó tag bent van-e egy hangcsatornában
    if not interaction.user.voice:
        await interaction.response.send_message("Előbb lépj be abba a hangcsatornába, ahova a botot hívni szeretnéd!", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    # Jelzzük a Discordnak, hogy dolgozunk (elkerüli az időtúllépési hibát)
    await interaction.response.defer()

    if vc:
        await vc.move_to(channel)
    else:
        vc = await channel.connect()

    # FFmpeg beállítások az automatikus újracsatlakozáshoz
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -af "silenceremove=start_periods=1:start_duration=0.1:start_threshold=-45dB:stop_periods=-1:stop_duration=0.8:stop_threshold=-45dB"'
    }

    source = discord.FFmpegPCMAudio(STREAM_URL, **ffmpeg_options)
    
    if not vc.is_playing():
        vc.play(source)
        await interaction.followup.send(f"🔊 Csatlakoztam a **{channel.name}** csatornához, a stream élő!")
    else:
        await interaction.followup.send(f"🔊 Átléptem a **{channel.name}** csatornába, a lejátszás folytatódik!")

@bot.tree.command(name="kilepes", description="A bot kilép a hangcsatornából")
async def kilepes(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("👋 Lecsatlakoztam a hangcsatornáról.")
    else:
        await interaction.response.send_message("Nem vagyok egyetlen hangcsatornában sem.", ephemeral=True)

# Indítás a Discord Bot Tokeneddel
bot.run(dotenv.get_key(dotenv.find_dotenv(), "DISCORD_BOT_TOKEN"))