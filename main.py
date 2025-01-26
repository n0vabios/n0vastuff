import nextcord
from nextcord import ButtonStyle, Interaction, SlashOption, File
from nextcord.ext import commands
import asyncio
import traceback
import io
import datetime
import re
from typing import Literal
import json
import requests
import colorama
from colorama import Fore, Back, Style
import time
import pyfiglet
import random
from serials import SerialManager
import os

SERVER_ID = 1326715338410430466
WELCOME_CHANNEL_ID = 1326741834466328707
MEMBER_ROLE_ID = 1326715769408720937
TICKET_CHANNEL_ID = 1327456661287207043
LOGS_CHANNEL_ID = 1332104348616102084
ERROR_CHANNEL_ID = 1326730285613846648
TICKET_LOGS_CHANNEL_ID = 1332108947439489045
ANNOUNCEMENTS_CHANNEL_ID = 1326736713988706315
APPLY_CHANNEL_ID = 1332141122813825044
BOT_COMMANDS_CHANNEL_ID = 1332148332868407346
TICKET_CATEGORY_ID = 1326752210746609746  

STAFF_ROLES = [
    1326715982604927006,
    1326715837184213023,
    1327721917565763584,
    1326715909976494153
]

BANNED_WORDS = [
    "nigger", "nigga", "fag", "faggot", "kkk", "nig"
]

ADMIN_ROLE_ID = 1327721917565763584

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)

warnings = {}
ticket_counters = {}

LEVEL_DATA = {}
try:
    with open('levels.json', 'r') as f:
        LEVEL_DATA = json.load(f)
except FileNotFoundError:
    LEVEL_DATA = {}

def save_levels():
    with open('levels.json', 'w') as f:
        json.dump(LEVEL_DATA, f)

try:
    with open('warnings.json', 'r') as f:
        warnings = json.load(f)
except FileNotFoundError:
    warnings = {}

def save_warnings():
    with open('warnings.json', 'w') as f:
        json.dump(warnings, f)

def parse_time(time_str: str) -> int:
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800,
        'mo': 2592000
    }
    
    match = re.match(r'(\d+)([smhdwmo]+)', time_str.lower())
    if not match:
        raise ValueError("Invalid time format")
    
    amount, unit = match.groups()
    return int(amount) * time_units[unit]

@bot.event
async def on_application_command_error(interaction: Interaction, error):
    error_channel = bot.get_channel(ERROR_CHANNEL_ID)
    error_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    
    error_embed = nextcord.Embed(
        title="Command Error",
        description=f"Command: {interaction.application_command.name}\nUser: {interaction.user.mention}\nError: ```{error_trace}```",
        color=0xff0000
    )
    
    await error_channel.send(embed=error_embed)
    await interaction.response.send_message("An error occurred while executing the command.", ephemeral=True)

def is_staff(member):
    return any(role.id in STAFF_ROLES for role in member.roles)

def has_admin_role(member):
    return any(role.id == ADMIN_ROLE_ID for role in member.roles)

async def log_command(interaction: Interaction, action: str, target: nextcord.Member = None, reason: str = None):
    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    
    log_embed = nextcord.Embed(
        title="Command Log",
        description=f"**Action:** {action}\n**Moderator:** {interaction.user.mention}",
        color=0x00ff00,
        timestamp=interaction.created_at
    )
    
    if target:
        log_embed.add_field(name="Target", value=f"{target.mention} ({target.id})")
    if reason:
        log_embed.add_field(name="Reason", value=reason)
        
    await logs_channel.send(embed=log_embed)

@bot.event
async def on_ready():
    try:
        print(f'Bot is ready as {bot.user}')
        bot.loop.create_task(rotate_presence())
        
        import threading
        threading.Thread(target=setup_console, daemon=True).start()
    except Exception as e:
        print(f"Error during startup: {e}")

@bot.event
async def on_member_join(member):
    if member.guild.id == SERVER_ID:
        welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
        member_role = member.guild.get_role(MEMBER_ROLE_ID)
        
        welcome_embed = nextcord.Embed(
            title="Welcome!",
            description=f"Welcome {member.mention} to the server! Enjoy your stay, or got to the ticket <#1327456661287207043> channel to get help! ",
            color=0x00ff00
        )
        
        await welcome_channel.send(embed=welcome_embed)
        await member.add_roles(member_role)

class TicketModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "Describe Your Issue",
            timeout=None,
        )

        self.issue = nextcord.ui.TextInput(
            label="Please describe your issue in detail",
            min_length=5,
            max_length=1000,
            required=True,
            placeholder="Enter your issue here...",
            style=nextcord.TextInputStyle.paragraph,
        )
        self.add_item(self.issue)

    async def callback(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        if user_id not in ticket_counters:
            ticket_counters[user_id] = 1
        else:
            ticket_counters[user_id] += 1

        channel_name = f"ticket-{interaction.user.name}-{ticket_counters[user_id]:02d}"
        
        overwrites = {
            interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
            interaction.user: nextcord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: nextcord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        for role_id in STAFF_ROLES:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = nextcord.PermissionOverwrite(read_messages=True, send_messages=True)

        
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        
        channel = await interaction.guild.create_text_channel(
            channel_name,
            category=category,  
            overwrites=overwrites
        )

        embed = nextcord.Embed(
            title="Welcome to n0va.one Support",
            description=(
                f"**User's Issue:**\n{self.issue.value}\n\n"
                "**For Bio Service Orders:**\n"
                "• Specify which bio package you're interested in\n"
                "• Share your preferred bio style\n"
                "• Include any specific themes\n"
                "• Mention any reference bios\n\n"
                "**For Other Inquiries:**\n"
                "• Custom bio requests\n"
                "• Partnership opportunities\n"
                "• General questions"
            ),
            color=0x800080
        )
        
        embed.set_footer(text="n0va.one - Premium Bio Services")
        await channel.send(f"<@&1326715837184213023>", embed=embed, view=TicketButtons())
        await interaction.response.send_message(f"Ticket created! Check {channel.mention}", ephemeral=True)

class ApplyModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "Bio Page Application",
            timeout=None,
        )

        self.display_name = nextcord.ui.TextInput(
            label="Display Name",
            required=True,
        )
        self.extension = nextcord.ui.TextInput(
            label="Desired Extension (n0va.one/yourextension)",
            required=True,
        )
        self.background = nextcord.ui.TextInput(
            label="Background URL (20MB or lower)",
            required=True,
        )
        self.profile_picture = nextcord.ui.TextInput(
            label="Profile Picture URL (20MB or lower)",
            required=True,
        )
        self.socials = nextcord.ui.TextInput(
            label="Socials (URLs, separate with commas)",
            style=nextcord.TextInputStyle.paragraph,
            required=True,
        )

        for item in [self.display_name, self.extension, self.background, 
                    self.profile_picture, self.socials]:
            self.add_item(item)

    async def callback(self, interaction: Interaction):
        channel = interaction.guild.get_channel(APPLY_CHANNEL_ID)
        embed = nextcord.Embed(
            title="New Bio Page Application",
            color=0x800080,
            timestamp=interaction.created_at
        )
        
        embed.add_field(name="Display Name", value=self.display_name.value, inline=False)
        embed.add_field(name="Extension", value=f"n0va.one/{self.extension.value}", inline=False)
        embed.add_field(name="Background", value=self.background.value, inline=False)
        embed.add_field(name="Profile Picture", value=self.profile_picture.value, inline=False)
        embed.add_field(name="Socials", value=self.socials.value, inline=False)
        embed.set_footer(text=f"Applied by {interaction.user}")

        await channel.send(embed=embed)
        await interaction.response.send_message("Your application has been submitted!", ephemeral=True)

class ConfirmClose(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="Yes", style=ButtonStyle.danger)
    async def confirm(self, button: nextcord.ui.Button, interaction: Interaction):
        if not (is_staff(interaction.user) or interaction.channel.name.startswith(f"ticket-{interaction.user.name}")):
            await interaction.response.send_message("Only staff members or ticket creator can close tickets!", ephemeral=True)
            return
        

        participants = set()
        messages = []
        async for message in interaction.channel.history(limit=None, oldest_first=True):
            participants.add(message.author)
            messages.append(f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author}: {message.content}")
        

        transcript = (
            f"Ticket: {interaction.channel.name}\n"
            f"Closed by: {interaction.user}\n"
            f"Participants: {', '.join([str(p) for p in participants])}\n"
            f"{'='*50}\n\n"
        ) + "\n".join(messages)
        

        ticket_logs_channel = interaction.guild.get_channel(TICKET_LOGS_CHANNEL_ID)
        transcript_embed = nextcord.Embed(
            title=f"Ticket Transcript - {interaction.channel.name}",
            description=f"Closed by: {interaction.user.mention}\nParticipants: {', '.join([p.mention for p in participants])}",
            color=0x800080
        )
        

        file = nextcord.File(
            fp=io.StringIO(transcript),
            filename=f"transcript-{interaction.channel.name}.txt"
        )
        await ticket_logs_channel.send(embed=transcript_embed, file=file)
        
        await log_command(interaction, "Ticket Closed")
        await interaction.channel.delete()

    @nextcord.ui.button(label="No", style=ButtonStyle.gray)
    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
        await interaction.response.send_message("Ticket closure cancelled.", ephemeral=True)

class TicketButtons(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimed_by = None

    @nextcord.ui.button(label="Claim Ticket", style=ButtonStyle.green)
    async def claim_ticket(self, button: nextcord.ui.Button, interaction: Interaction):
        if not is_staff(interaction.user):
            await interaction.response.send_message("Only staff members can claim tickets!", ephemeral=True)
            return
        
        if self.claimed_by:
            await interaction.response.send_message(f"This ticket is already claimed by {self.claimed_by.mention}!", ephemeral=True)
            return
        
        self.claimed_by = interaction.user
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"Ticket claimed by {interaction.user.mention}")

    @nextcord.ui.button(label="Ping Staff", style=ButtonStyle.primary)
    async def ping_staff(self, button: nextcord.ui.Button, interaction: Interaction):
        await interaction.response.send_message(
            f"<@&1326715837184213023> - Staff assistance requested!", 
            allowed_mentions=nextcord.AllowedMentions(roles=True)
        )

    @nextcord.ui.button(label="Close Ticket", style=ButtonStyle.danger)
    async def close_ticket(self, button: nextcord.ui.Button, interaction: Interaction):
        await interaction.response.send_message(
            "Are you sure you want to close this ticket?",
            view=ConfirmClose(),
            ephemeral=True
        )

@bot.slash_command(guild_ids=[SERVER_ID])
async def ban(interaction: Interaction, member: nextcord.Member, reason: str = None):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    await interaction.response.defer()
    await member.ban(reason=reason)
    await log_command(interaction, "Ban", member, reason)
    await interaction.followup.send(f"{member.mention} has been banned. Reason: {reason}")

@bot.slash_command(guild_ids=[SERVER_ID])
async def kick(interaction: Interaction, member: nextcord.Member, reason: str = None):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    await interaction.response.defer()
    await member.kick(reason=reason)
    await log_command(interaction, "Kick", member, reason)
    await interaction.followup.send(f"{member.mention} has been kicked. Reason: {reason}")

@bot.slash_command(guild_ids=[SERVER_ID])
async def timeout(interaction: Interaction, member: nextcord.Member, duration: str, reason: str = None):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        duration_seconds = parse_time(duration)
        duration_delta = datetime.timedelta(seconds=duration_seconds)
        await member.timeout(until=datetime.datetime.now() + duration_delta, reason=reason)
        await log_command(interaction, f"Timeout ({duration})", member, reason)
        await interaction.followup.send(f"{member.mention} has been timed out for {duration}. Reason: {reason}")
    except ValueError:
        await interaction.response.send_message("Invalid duration format! Use format like: 30m, 1h, 1d", ephemeral=True)

@bot.slash_command(guild_ids=[SERVER_ID])
async def mute(interaction: Interaction, member: nextcord.Member, reason: str = None):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    await interaction.response.defer()
    duration_delta = datetime.timedelta(days=28)
    await member.timeout(until=datetime.datetime.now() + duration_delta, reason=reason)
    await log_command(interaction, "Mute", member, reason)
    await interaction.followup.send(f"{member.mention} has been muted. Reason: {reason}")

@bot.slash_command(guild_ids=[SERVER_ID])
async def ticket(interaction: Interaction):
    await interaction.response.send_modal(TicketModal())

@bot.slash_command(guild_ids=[SERVER_ID])
async def apply(interaction: Interaction):
    if interaction.channel.id != BOT_COMMANDS_CHANNEL_ID:
        await interaction.response.send_message(f"Please use this command in <#{BOT_COMMANDS_CHANNEL_ID}>!", ephemeral=True)
        return
    
    apply_channel = interaction.guild.get_channel(APPLY_CHANNEL_ID)
    if not apply_channel:
        await interaction.response.send_message("Error: Applications channel not found!", ephemeral=True)
        return
        
    await interaction.response.send_modal(ApplyModal())

@bot.slash_command(guild_ids=[SERVER_ID])
async def warn(interaction: Interaction, member: nextcord.Member, reason: str):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    await interaction.response.defer()
    user_id = str(member.id)
    if user_id not in warnings:
        warnings[user_id] = []
    
    warnings[user_id].append({
        'reason': reason,
        'moderator': interaction.user.id,
        'timestamp': datetime.datetime.now().isoformat()
    })
    save_warnings()
    
    await log_command(interaction, "Warning", member, reason)
    await interaction.followup.send(f"{member.mention} has been warned. Reason: {reason}")

@bot.slash_command(guild_ids=[SERVER_ID])
async def warnings(interaction: Interaction, member: nextcord.Member):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    user_id = str(member.id)
    if user_id not in warnings or not warnings[user_id]:
        await interaction.response.send_message(f"{member.mention} has no warnings.", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title=f"Warnings for {member}",
        color=0x800080
    )
    
    for i, warning in enumerate(warnings[user_id], 1):
        moderator = interaction.guild.get_member(warning['moderator'])
        mod_name = moderator.name if moderator else "Unknown Moderator"
        timestamp = datetime.datetime.fromisoformat(warning['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        embed.add_field(
            name=f"Warning {i}",
            value=f"Reason: {warning['reason']}\nModerator: {mod_name}\nDate: {timestamp}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.slash_command(guild_ids=[SERVER_ID])
async def clearwarnings(interaction: Interaction, member: nextcord.Member):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    user_id = str(member.id)
    if user_id in warnings:
        warnings[user_id] = []
        save_warnings()
    
    await log_command(interaction, "Warnings Cleared", member)
    await interaction.response.send_message(f"Cleared all warnings for {member.mention}")

@bot.slash_command(guild_ids=[SERVER_ID])
async def ghost(interaction: Interaction):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    await bot.change_presence(status=nextcord.Status.invisible)
    await log_command(interaction, "Ghost Mode Enabled")
    await interaction.response.send_message("Ghost mode enabled. Bot is now invisible.", ephemeral=True)

@bot.slash_command(guild_ids=[SERVER_ID])
async def unghost(interaction: Interaction):
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    await bot.change_presence(
        status=nextcord.Status.online,
        activity=nextcord.Streaming(
            name="n0va.one - Elevate your presence",
            url="https://twitch.tv/n0va",
            details="with one powerful link"
        )
    )
    await log_command(interaction, "Ghost Mode Disabled")
    await interaction.response.send_message("Ghost mode disabled. Bot is now visible.", ephemeral=True)

@bot.slash_command(guild_ids=[SERVER_ID])
async def help(interaction: Interaction):
    embed = nextcord.Embed(
        title="n0va.one Bot Commands",
        description="Here are all available commands:",
        color=0x800080
    )
    
    if is_staff(interaction.user):
        embed.add_field(
            name="Staff Commands",
            value=(
                "`/ban` - Ban a member\n"
                "`/unban` - Unban a member using their ID\n"
                "`/kick` - Kick a member\n"
                "`/timeout` - Timeout a member\n"
                "`/mute` - Mute a member\n"
                "`/warn` - Warn a member\n"
                "`/warnings` - View member warnings\n"
                "`/clearwarnings` - Clear member warnings\n"
                "`/ghost` - Make bot invisible\n"
                "`/unghost` - Make bot visible\n"
                "`/announce` - Make an announcement\n"
                "`/talk` - Send a custom embed message"
            ),
            inline=False
        )
    
    embed.add_field(
        name="General Commands",
        value=(
            "`/ticket` - Create a support ticket\n"
            "`/apply` - Apply for a bio page\n"
            "`/help` - Show this help message\n"
            "`/level` - Check your level\n"
            "`/hawk` - Check bot latency\n"
            "`/lookup` - Check if a n0va.one extension is available"
        ),
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(guild_ids=[SERVER_ID])
async def announce(
    interaction: Interaction, 
    title: str,
    message: str,
    image_url: str = None,
    ping_type: Literal['everyone', 'here', 'none'] = 'none'
):
    """Make an announcement in the announcements channel"""
    if not has_admin_role(interaction.user):
        await interaction.response.send_message("❌ You need the admin role to use this command!", ephemeral=True)
        return

    try:
        await interaction.response.defer(ephemeral=True)
        
        announcements_channel = interaction.guild.get_channel(ANNOUNCEMENTS_CHANNEL_ID)
        if not announcements_channel:
            await interaction.followup.send("Error: Announcements channel not found!", ephemeral=True)
            return

        formatted_message = message.replace('\\n', '\n')

        announce_embed = nextcord.Embed(
            title=title,
            description=formatted_message,
            color=0x800080,
            timestamp=datetime.datetime.now()
        )
        
        if image_url:
            try:
                announce_embed.set_image(url=image_url)
            except:
                await interaction.followup.send("Invalid image URL provided!", ephemeral=True)
                return
                
        announce_embed.set_footer(text=f"Announced by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        
        content = None
        if ping_type == 'everyone':
            content = '@everyone'
        elif ping_type == 'here':
            content = '@here'
        
        await announcements_channel.send(content=content, embed=announce_embed)
        await interaction.followup.send("Announcement sent!", ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    user_id = str(message.author.id)
    if user_id not in LEVEL_DATA:
        LEVEL_DATA[user_id] = {"xp": 0, "level": 0}
    
    xp_gain = random.randint(5, 10)
    LEVEL_DATA[user_id]["xp"] += xp_gain
    
    current_level = LEVEL_DATA[user_id]["level"]
    new_level = min(15, LEVEL_DATA[user_id]["xp"] // 400)  # Cap at level 15
    
    if new_level > current_level:
        LEVEL_DATA[user_id]["level"] = new_level
        save_levels()
        
        embed = nextcord.Embed(
            title="Level Up! 🎉",
            description=f"{message.author.mention} has reached level {new_level}!",
            color=0x00ff00
        )
        await message.channel.send(embed=embed)
    
    content = message.content.lower()
    
    for word in BANNED_WORDS:
        if word in content:
            await auto_mute_user(message, f"Automatic mute: Used banned word '{word}'")
            return

    if not is_staff(message.author):
        if "http://" in content or "https://" in content:
            await auto_mute_user(message, "Automatic mute: Sent unauthorized link")
            return
        
        if "discord.gg" in content or "discord.com/invite" in content:
            await auto_mute_user(message, "Automatic mute: Sent Discord invite link")
            return

    await bot.process_commands(message)

async def auto_mute_user(message, reason):
    member = message.author
    
    # Timeout for 1 hour
    duration_delta = datetime.timedelta(hours=1)
    await member.timeout(until=datetime.datetime.now() + duration_delta, reason=reason)
    
    logs_channel = message.guild.get_channel(LOGS_CHANNEL_ID)
    log_embed = nextcord.Embed(
        title="Auto-Mute",
        description=f"**User:** {member.mention}\n**Reason:** {reason}",
        color=0xFF0000,
        timestamp=datetime.datetime.now()
    )
    await logs_channel.send(embed=log_embed)
    
    try:
        await message.channel.send(f"{member.mention} has been automatically muted for 1 hour for violating server rules.", delete_after=10)
    except:
        pass
    
    try:
        await message.delete()
    except:
        pass

async def rotate_presence():
    presences = [
        ("apply do /apply", "https://twitch.tv/n0va"),
        ("Good links @ n0va.one", "https://twitch.tv/n0va"),
        ("rip juju", "https://twitch.tv/n0va"),
        ("n0va.one - Elevate your presence", "https://twitch.tv/n0va"),
        ("best place to share yourselves", "https://twitch.tv/n0va"),
        ("questions? make a ticket", "https://twitch.tv/n0va"),
        ("made by the best dev - luxx", "https://twitch.tv/n0va"),
        ("battleye is a bitch", "https://twitch.tv/n0va"),
        ("hawk tuah", "https://twitch.tv/n0va"),
        ("LLJJ", "https://twitch.tv/n0va"),
        ("Jordan is the best co owner", "https://twitch.tv/n0va"),
        ("im racist", "https://twitch.tv/n0va"),
        ("killer is fat", "https://twitch.tv/n0va"),
        ("giggity", "https://twitch.tv/n0va"),
        ("the only n word that we drop", "https://twitch.tv/n0va"),
        ("on a daily basis at my house is", "https://twitch.tv/n0va"),
        ("reggin. fuck reggins", "https://twitch.tv/n0va")
    ]
    while True:
        for text, url in presences:
            await bot.change_presence(
                activity=nextcord.Streaming(
                    name=text,
                    url=url
                )
            )
            await asyncio.sleep(2)  # Change every 30 seconds

@bot.slash_command(guild_ids=[SERVER_ID])
async def unban(interaction: Interaction, user_id: str, reason: str = None):
    """Unban a user using their ID"""
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)
        await log_command(interaction, "Unban", user, reason)
        await interaction.response.send_message(f"User {user.mention} ({user_id}) has been unbanned. Reason: {reason}")
    except ValueError:
        await interaction.response.send_message("Invalid user ID provided!", ephemeral=True)
    except nextcord.NotFound:
        await interaction.response.send_message("User not found!", ephemeral=True)
    except nextcord.HTTPException as e:
        await interaction.response.send_message(f"Failed to unban user: {str(e)}", ephemeral=True)

@bot.slash_command(guild_ids=[SERVER_ID])
async def talk(
    interaction: Interaction, 
    message: str, 
    image_url: str = None, 
    color: str = None,
    title: str = None,
    mentions: str = None,
    ping_type: Literal['everyone', 'here', 'none'] = 'none'
):
    if not has_admin_role(interaction.user):
        await interaction.response.send_message("❌ You need the admin role to use this command!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)

    formatted_message = message.replace('\\n', '\n')
    
    try:
        embed_color = int(color.strip('#'), 16) if color else 0x800080
    except ValueError:
        embed_color = 0x800080
    
    embed = nextcord.Embed(
        title=title if title else None,
        description=formatted_message,
        color=embed_color
    )
    
    if image_url:
        try:
            embed.set_image(url=image_url)
        except:
            await interaction.followup.send("Invalid image URL provided!", ephemeral=True)
            return
    
    mention_list = []
    
    if ping_type == 'everyone':
        mention_list.append('@everyone')
    elif ping_type == 'here':
        mention_list.append('@here')
    
    if mentions:
        try:
            for user_id in mentions.split():
                user = await bot.fetch_user(int(user_id))
                mention_list.append(user.mention)
        except (ValueError, nextcord.NotFound):
            await interaction.followup.send("Invalid user ID provided in mentions!", ephemeral=True)
            return
    
    content = ' '.join(mention_list) if mention_list else None
    
    await interaction.channel.send(content=content, embed=embed)
    await interaction.followup.send("Message sent!", ephemeral=True)

@bot.slash_command(guild_ids=[SERVER_ID])
async def hawk(interaction: Interaction):
    """Check bot latency"""
    start_time = time.time()
    await interaction.response.send_message("Calculating...")
    end_time = time.time()
    
    latency = round((end_time - start_time) * 1000)
    await interaction.edit_original_message(content=f"tuah! 🦅 (`{latency}ms`)")

@bot.slash_command(guild_ids=[SERVER_ID])
async def lookup(interaction: Interaction, extension: str):
    """Look up if a n0va.one extension is available"""
    if interaction.channel.id != BOT_COMMANDS_CHANNEL_ID:
        await interaction.response.send_message(f"Please use this command in <#{BOT_COMMANDS_CHANNEL_ID}>!", ephemeral=True)
        return
    
    url = f"https://n0va.one/{extension}"
    
    try:
        response = requests.get(url)
        if response.status_code == 404:
            await interaction.response.send_message(f"🟢 `{url}` - This extension is available!")
        else:
            await interaction.response.send_message(f"🔴 `{url}` - This extension is taken or the user has been banned.")
    except:
        await interaction.response.send_message("Failed to check extension availability.", ephemeral=True)


@bot.slash_command(guild_ids=[SERVER_ID])
async def level(interaction: Interaction, member: nextcord.Member = None):
    """Check your or someone else's level"""
    target = member or interaction.user
    user_id = str(target.id)
    
    if user_id not in LEVEL_DATA:
        LEVEL_DATA[user_id] = {"xp": 0, "level": 0}
    
    data = LEVEL_DATA[user_id]
    current_xp = data["xp"]
    current_level = data["level"]
    xp_for_next = (current_level + 1) * 400 if current_level < 15 else "MAX"
    
    embed = nextcord.Embed(
        title=f"Level Info - {target.name}",
        color=0x800080
    )
    embed.add_field(name="Level", value=current_level, inline=True)
    embed.add_field(name="XP", value=current_xp, inline=True)
    if xp_for_next != "MAX":
        embed.add_field(name="Next Level", value=f"{current_xp}/{xp_for_next} XP", inline=True)
    else:
        embed.add_field(name="Status", value="Max Level Reached!", inline=True)
    
    await interaction.response.send_message(embed=embed)


def setup_console():
    try:
        colorama.init()
        ascii_art = pyfiglet.figlet_format("Bot Running")
        
        while True:
            colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
            for color in colors:
                print(Style.BRIGHT + color + ascii_art + Style.RESET_ALL, end='\r')
                time.sleep(5)  # Changed from 0.5 to 5 seconds
    except Exception as e:
        print(f"Console setup error: {e}")

serial_manager = SerialManager()

@bot.slash_command(guild_ids=[SERVER_ID])
async def genkey(interaction: Interaction, amount: int = 1, duration: Literal['never', '30d'] = '30d'):
    """Generate serial keys"""
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Please specify an amount between 1 and 100", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)  # Defer the response to prevent timeout
    
    days = -1 if duration == 'never' else 30
    keys = []
    for _ in range(amount):
        serial = serial_manager.generate_serial(days)
        keys.append(serial)
    
    embed = nextcord.Embed(
        title="Serial Keys Generated",
        description=f"Generated {amount} {'key' if amount == 1 else 'keys'}\nDuration: {'Never Expires' if duration == 'never' else '30 days'}",
        color=0x800080
    )
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"keys_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        for key in keys:
            f.write(f"{key}\n")
    
    file = nextcord.File(filename)
    await interaction.followup.send(embed=embed, file=file, ephemeral=True)
    
    # Clean up the file after sending
    try:
        os.remove(filename)
    except:
        pass

@bot.slash_command(guild_ids=[SERVER_ID])
async def activate(interaction: Interaction, serial: str):
    """Activate a serial key"""
    success, message = serial_manager.verify_serial(serial, str(interaction.user.id))
    await interaction.response.send_message(message, ephemeral=True)

@bot.slash_command(guild_ids=[SERVER_ID])
async def serialinfo(interaction: Interaction):
    """Check your serial key information"""
    serial = serial_manager.get_user_serial(str(interaction.user.id))
    if not serial:
        await interaction.response.send_message("You don't have an active serial key.", ephemeral=True)
        return
        
    info = serial_manager.get_serial_info(serial)
    
    embed = nextcord.Embed(
        title="Serial Key Information",
        color=0x800080
    )
    embed.add_field(name="Serial", value=serial, inline=False)
    
    if info["expiry_date"] == "never":
        embed.add_field(name="Expiry Date", value="Never Expires", inline=False)
    else:
        expiry_date = datetime.datetime.fromisoformat(info["expiry_date"])
        embed.add_field(name="Expiry Date", value=expiry_date.strftime('%Y-%m-%d %H:%M:%S'), inline=False)
    
    duration = "Permanent" if info["duration_days"] == -1 else f"{info['duration_days']} days"
    embed.add_field(name="Duration", value=duration, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(guild_ids=[SERVER_ID])
async def purge(interaction: Interaction, amount: int):
    """Purge messages from the channel
    Parameters
    ----------
    amount: Number of messages to delete (1-100)
    """
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Please specify an amount between 1 and 100", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)
    await log_command(interaction, "Purge", reason=f"Purged {len(deleted)} messages from {interaction.channel.mention}")

@bot.slash_command(guild_ids=[SERVER_ID])
async def nuke(interaction: Interaction):
    """Nuke the current channel (recreate with same permissions)"""
    if not is_staff(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    # Store channel properties
    channel = interaction.channel
    category = channel.category
    position = channel.position
    name = channel.name
    topic = channel.topic
    overwrites = channel.overwrites
    
    # Create new channel
    try:
        await channel.delete()
        new_channel = await interaction.guild.create_text_channel(
            name=name,
            category=category,
            topic=topic,
            position=position,
            overwrites=overwrites
        )
        await log_command(interaction, "Nuke", reason=f"Nuked channel {name}")
        
        # Send confirmation in new channel
        embed = nextcord.Embed(
            title="Channel Nuked 💥",
            description="This channel has been nuked by a staff member.",
            color=0xFF0000
        )
        await new_channel.send(embed=embed)
        
        # Send confirmation to staff member
        await interaction.followup.send(f"Channel has been nuked and recreated: {new_channel.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error nuking channel: {str(e)}", ephemeral=True)

bot.run('MTMzMjE0OTUyODgzNjcwMjI2OQ.GuipiF.CMBVukkyV1Txe-7O7OclYOQabBeVhy9qsloSZc')

