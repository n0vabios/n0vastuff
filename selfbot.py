import discord
import asyncio
import random
import colorama
from colorama import Fore, Style
import pyfiglet
import json
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import webbrowser
from win10toast import ToastNotifier
import os
from datetime import datetime
from bs4 import BeautifulSoup
import openai
import aiohttp
import base64
import logging
import sys
import subprocess
import pkg_resources
from tray import TrayIcon
import win32gui
import win32con
import platform
import threading
from google.protobuf.json_format import MessageToDict

logging.getLogger('discord.state').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)

# Add at the top after imports
def handle_exception(loop, context):
    # Extract exception details
    exception = context.get('exception', context['message'])
    print(f"Caught exception: {exception}")
    
    # Prevent crash on common errors
    if isinstance(exception, (discord.errors.HTTPException, 
                            aiohttp.ClientError,
                            ConnectionResetError,
                            asyncio.exceptions.TimeoutError)):
        return
    
    # Log other errors but don't crash
    print(f"Unhandled exception: {exception}")

class SelfBot(discord.Client):
    def __init__(self):
        # Initialize with minimal required parameters for user account
        super().__init__(self_bot=True, status=discord.Status.online)  # This is the correct parameter for user accounts
        self.setup_complete = False
        self._exception_handler = handle_exception
        
    async def setup_hook(self):
        self.loop.set_exception_handler(self._exception_handler)
        self.setup_complete = True

client = SelfBot()

toaster = ToastNotifier()

# Add required packages
required_packages = {
    'discord.py-self': 'discord',
    'pillow': 'PIL',
    'colorama': 'colorama',
    'pyfiglet': 'pyfiglet',
    'win10toast': 'win10toast',
    'beautifulsoup4': 'bs4',
    'requests': 'requests',
    'aiohttp': 'aiohttp'
}

# Default config structure
default_config = {
    "token": "",
    "header": {
        "text": "[ n0va.one ]",
        "color": "purple"  
    },
    "footer": {
        "text": "[ made by luxx ]",
        "color": "purple"
    },
    "afk": {
        "enabled": False,
        "message": "I'm currently AFK",
        "pinged_by": []
    },
    "ai": {
        "openai_key": "",
        "last_response": ""
    },
    "message_timer": 5,
    "custom_status_messages": [],
    "hide": {
        "errors": False,
        "status": False
    }
}

def create_default_config():
    with open('config.json', 'w') as f:
        json.dump(default_config, f, indent=4)
    return default_config

# Config for customizable parts
config = {
    "header": {
        "text": "[ n0va.one ]",
        "color": "purple"  
    },
    "footer": {
        "text": "[ made by luxx ]",
        "color": "purple"
    },
    "afk": {
        "enabled": False,
        "message": "I'm currently AFK",
        "pinged_by": []
    },
    "ai": {
        "openai_key": "",
        "last_response": ""
    },
    "message_timer": 5  # Default deletion time in seconds
}

colors = {
    "purple": "35",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "pink": "95",
    "light_blue": "36",
    "dark_blue": "34"
}

# Save/Load config
def save_config():
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.YELLOW}No config file found, creating default...{Style.RESET_ALL}")
        return create_default_config()
    except json.JSONDecodeError:
        print(f"{Fore.RED}Invalid config file, creating default...{Style.RESET_ALL}")
        return create_default_config()

config = load_config()

custom_status_messages = [
    "🌟 n0va.one - Elevate your presence",
    "🔥 best place to share yourselves",
    "❓ i vape",
    "👑 made by the best dev - luxx",
    "💥 battleye is a good soul",
    "🙏 hawk tuah",
    "✨ im goated",
    "🌎 worldwide",
    "💫 stay elevated",
    "🚀 to the moon",
    "💯 always on top",
    "⚡ powered by n0va",
    "🎮 gaming hard",
    "🎯 aim god",
    "💪 getting stronger"
]

# Add this list of emojis at the top with your other variables
status_emojis = [
    "🌟", "🔥", "❓", "👑", "💥", "🙏", "✨", "🌎", "🌟", 
    "��", "💯", "⚡", "🎮", "🎯", "💪", "🎭", "🌈", "🎪",
    "🎨", "🎬", "🎤", "🎧", "🎵", "🎶", "🌙", "⭐", "✅"
]

# First, update the global mimicking variable to store both ID and channel
mimicking = {"user": None, "channel": None}

class StatusManager:
    def __init__(self):
        self.status_messages = []
        self.current_index = 0
        self.is_rotating = False
        
    def add_status(self, status):
        if status not in self.status_messages:
            self.status_messages.append(status)
            return True
        return False
        
    def remove_status(self, index):
        if 0 <= index < len(self.status_messages):
            return self.status_messages.pop(index)
        return None
        
    def get_next_status(self):
        if not self.status_messages:
            return None
        status = self.status_messages[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.status_messages)
        return status
        
    def clear_statuses(self):
        self.status_messages.clear()
        self.current_index = 0

# Initialize status manager
status_manager = StatusManager()

# Add this after status_manager initialization
for status in custom_status_messages:
    status_manager.add_status(status)

@client.event
async def on_ready():
    ascii_art = pyfiglet.figlet_format("n0va selfbot")
    print(f"{Fore.MAGENTA}{ascii_art}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Connected as: {client.user}{Style.RESET_ALL}")
    
    # Start status rotation in a separate task
    client.loop.create_task(status_rotation())

# Add this function for clearing terminal
def clear_terminal():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

# Update terminal_commands function
def terminal_commands():
    tray_icon = None
    client_running = False
    loop = None
    
    # Show ASCII art on startup
    clear_terminal()
    ascii_art = pyfiglet.figlet_format("n0va selfbot")
    print(f"{Fore.MAGENTA}{ascii_art}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Type 'help' for commands{Style.RESET_ALL}\n")
    
    while True:
        try:
            cmd = input(f"{Fore.CYAN}> {Style.RESET_ALL}").lower().strip()
            
            # Check if the command is empty
            if not cmd:
                continue  # Skip empty commands
            
            if cmd == "start":
                if not client_running:
                    print(f"{Fore.GREEN}Starting selfbot...{Style.RESET_ALL}")
                    # Create new event loop for the client
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.create_task(main())
                    threading.Thread(target=lambda: loop.run_forever(), daemon=True).start()
                    client_running = True
                else:
                    print(f"{Fore.YELLOW}Selfbot is already running{Style.RESET_ALL}")
            
            elif cmd == "clear":
                clear_terminal()
                print(f"{Fore.MAGENTA}{ascii_art}{Style.RESET_ALL}")
                
            elif cmd == "hide --error":
                config['hide']['errors'] = not config['hide']['errors']
                save_config()
                status = "hidden" if config['hide']['errors'] else "shown"
                print(f"{Fore.GREEN}Error messages will now be {status}{Style.RESET_ALL}")
                
            elif cmd == "hide --status":
                config['hide']['status'] = not config['hide']['status']
                save_config()
                status = "hidden" if config['hide']['status'] else "shown"
                print(f"{Fore.GREEN}Status updates will now be {status}{Style.RESET_ALL}")
            
            elif cmd == "exit":
                print("Shutting down...")
                if loop and loop.is_running():
                    loop.call_soon_threadsafe(lambda: loop.create_task(shutdown()))
                    loop.call_soon_threadsafe(loop.stop)
                break
                
            elif cmd == "help":
                print(f"""
{Fore.GREEN}Available Commands:{Style.RESET_ALL}
help          - Show this help message
start         - Start the selfbot
clear         - Clear terminal
tray          - Minimize to system tray
settoken      - Set Discord token
hide --error  - Toggle error messages
hide --status - Toggle status updates
setstatus     - Add new status message
liststatus    - Show all status messages
delstatus     - Remove a status message
exit          - Exit the selfbot
""")
            
            elif cmd == "tray":
                if not tray_icon:
                    tray_icon = TrayIcon(show_console)
                    threading.Thread(target=tray_icon.run, daemon=True).start()
                hide_console()
                
            elif cmd == "settoken":
                token = input("Enter your Discord token: ").strip()
                config['token'] = token
                save_config()
                print(f"{Fore.GREEN}Token updated!{Style.RESET_ALL}")
                
            elif cmd.startswith("setstatus"):
                status = cmd[10:].strip()
                if status:
                    config['custom_status_messages'].append(status)
                    save_config()
                    print(f"{Fore.GREEN}Added new status: {status}{Style.RESET_ALL}")
                
            elif cmd == "liststatus":
                if config['custom_status_messages']:
                    for i, status in enumerate(config['custom_status_messages'], 1):
                        print(f"{i}. {status}")
                else:
                    print(f"{Fore.YELLOW}No custom status messages set{Style.RESET_ALL}")
                    
            elif cmd.startswith("delstatus"):
                try:
                    index = int(cmd[10:].strip()) - 1
                    if 0 <= index < len(config['custom_status_messages']):
                        removed = config['custom_status_messages'].pop(index)
                        save_config()
                        print(f"{Fore.GREEN}Removed status: {removed}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Invalid status index{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}Please specify a valid number{Style.RESET_ALL}")

        except Exception as e:
            if not config['hide']['errors']:
                print(f"{Fore.RED}Command error: {e}{Style.RESET_ALL}")

# Update the status rotation to respect hide setting
async def status_rotation():
    while True:
        try:
            if status_manager.status_messages:
                status = status_manager.get_next_status()
                if status:
                    # Create a proper activity object
                    game = discord.Activity(
                        type=discord.ActivityType.playing,
                        name=status
                    )
                    await client.change_presence(activity=game)
                    if not config['hide']['status']:
                        print(f"{Fore.CYAN}Status updated: {status}{Style.RESET_ALL}")
            await asyncio.sleep(10)
        except Exception as e:
            if not config['hide']['errors']:
                print(f"{Fore.RED}Status error: {e}{Style.RESET_ALL}")
            await asyncio.sleep(30)  # Longer delay on error

# Add this function to handle incoming messages
@client.event
async def on_message(message):
    global mimicking  # Single global declaration at the start
    
    # Check if we're mimicking and this is the right user and channel
    if (mimicking["user"] and message.author.id == mimicking["user"] 
        and message.channel.id == mimicking["channel"]
        and message.author != client.user):
        try:
            # For DMs or channels without webhook support, just send a normal message
            content = f"{message.author.name}: {message.content}"
            
            # Handle attachments
            files = []
            for attachment in message.attachments:
                files.append(await attachment.to_file())
                
            # Send the message with any attachments
            await message.channel.send(content, files=files)
            
        except Exception as e:
            print(f"Mimic error: {e}")
            pass

    if message.author != client.user:
        if config['afk']['enabled'] and (message.mentions and client.user in message.mentions or 
            isinstance(message.channel, discord.DMChannel)):
            config['afk']['pinged_by'].append(message.author.id)
            response = f"AFK: {config['afk']['message']}\nPinged by: {message.author.mention}"
            msg = await message.channel.send(create_message(response))
            toaster.show_toast("AFK Alert", f"{message.author.name} mentioned you!", duration=5)
            await asyncio.sleep(config['message_timer'])
            await msg.delete()
        return

    if message.content.startswith('.changehead'):
        await message.delete()
        new_header = message.content[11:].strip()
        if new_header:
            config['header']['text'] = new_header
            save_config()
            msg = await message.channel.send(create_message("Header updated successfully!"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content.startswith('.changeftr'):
        await message.delete()
        new_footer = message.content[10:].strip()
        if new_footer:
            config['footer']['text'] = new_footer
            save_config()
            msg = await message.channel.send(create_message("Footer updated successfully!"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content.startswith('.afk'):
        await message.delete()
        custom_message = message.content[5:].strip()
        config['afk']['enabled'] = True
        config['afk']['message'] = custom_message if custom_message else "I'm currently AFK"
        save_config()
        msg = await message.channel.send(create_message(f"AFK enabled: {config['afk']['message']}"))
        await asyncio.sleep(config['message_timer'])
        await msg.delete()

    elif message.content == '.back':
        await message.delete()
        config['afk']['enabled'] = False
        save_config()
        msg = await message.channel.send(create_message("AFK disabled"))
        await asyncio.sleep(config['message_timer'])
        await msg.delete()

    elif message.content.startswith('.gay'):
        await message.delete()
        try:
            user = message.mentions[0]
        except:
            user = message.author
        
        gay_meter = random.randint(0, 100)
        meter = "🏳️‍🌈" * (gay_meter // 10) + "+" * (10 - gay_meter // 10)
        content = f"Gay Meter for {user.name}\n{meter}\n{gay_meter}% gay"
        
        msg = await message.channel.send(create_message(content))
        await asyncio.sleep(config['message_timer'])
        await msg.delete()

    elif message.content.startswith('.mimic'):
        await message.delete()
        try:
            if len(message.mentions) > 0:
                user = message.mentions[0]
                mimicking = {
                    "user": user.id,
                    "channel": message.channel.id
                }
                msg = await message.channel.send(create_message(f"Now mimicking: {user.name} in this channel"))
                await asyncio.sleep(config['message_timer'])
                await msg.delete()
        except Exception as e:
            print(f"Mimic error: {e}")
            pass

    elif message.content == '.stopmimic':
        await message.delete()
        if mimicking["user"]:
            mimicking = {"user": None, "channel": None}
            msg = await message.channel.send(create_message("Stopped mimicking"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content.startswith('.ping'):
        await message.delete()
        latency = round(client.latency * 1000)
        msg = await message.channel.send(create_message(f"Pong! {latency}ms"))
        await asyncio.sleep(config['message_timer'])
        await msg.delete()

    elif message.content.startswith('.av'):
        await message.delete()
        try:
            user = message.mentions[0]
        except:
            user = message.author
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        msg = await message.channel.send(avatar_url)
        await asyncio.sleep(config['message_timer'])
        await msg.delete()

    elif message.content.startswith('.purge'):
        await message.delete()
        try:
            amount = int(message.content.split()[1])
            async for msg in message.channel.history(limit=amount):
                if msg.author == client.user:
                    try:
                        await msg.delete()
                        await asyncio.sleep(0.3)
                    except:
                        continue
        except:
            pass

    elif message.content.startswith('.userinfo'):
        await message.delete()
        try:
            user = message.mentions[0]
        except:
            user = message.author
            
        content = f"""User Info for {user.name}
ID: {user.id}
Created: {user.created_at.strftime('%Y-%m-%d')}
Username: {user.name}#{user.discriminator}"""
        
        msg = await message.channel.send(create_message(content))
        await asyncio.sleep(config['message_timer'])
        await msg.delete()

    elif message.content == '.sessions':
        await message.delete()
        headers = {'Authorization': client.http.token}
        r = requests.get('https://discord.com/api/v9/auth/sessions', headers=headers)
        if r.status_code == 200:
            sessions = r.json()
            content = "Active Sessions:\n"
            for session in sessions:
                content += f"Client: {session.get('client_info', 'Unknown')}\n"
                content += f"Location: {session.get('location', 'Unknown')}\n"
            toaster.show_toast("Sessions", f"Found {len(sessions)} active sessions", duration=5)
            msg = await message.channel.send(create_message(content))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content.startswith('.search'):
        await message.delete()
        query = message.content[8:].strip()
        if query:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            msg = await message.channel.send(create_message(f"Searching for: {query}"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content.startswith('.massdm'):
        await message.delete()
        text = message.content[8:].strip()
        if text:
            count = 0
            for channel in client.private_channels:
                try:
                    await channel.send(text)
                    count += 1
                    await asyncio.sleep(1)
                except:
                    continue
            msg = await message.channel.send(create_message(f"Sent message to {count} DMs"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content.startswith('.headercolor'):
        await message.delete()
        color = message.content[12:].strip().lower()
        if color in colors:
            config['header']['color'] = color
            save_config()
            msg = await message.channel.send(create_message("Header color updated!"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content.startswith('.footercolor'):
        await message.delete()
        color = message.content[12:].strip().lower()
        if color in colors:
            config['footer']['color'] = color
            save_config()
            msg = await message.channel.send(create_message("Footer color updated!"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content.startswith('.cmds'):
        await message.delete()
        pages = {
            "1": """[Main Commands]
.ping - Check latency
.av [@user] - Show avatar
.purge <amount> - Delete your messages
.userinfo [@user] - Show user info
.gay [@user] - Check gay meter
.mimic @user <text> - Mimic a user
.cmds page <1-5> - Show commands""",

            "2": """[Status Commands]
.online - Set status to Online
.idle - Set status to Idle
.dnd - Set status to Do Not Disturb
.setstatus <text> - Add new status message
.liststatus - Show all status messages
.delstatus <number> - Remove status message""",

            "3": """[Customization]
.changehead <text> - Change header text
.changeftr <text> - Change footer text
.headercolor <color> - Change header color
.footercolor <color> - Change footer color

Available Colors:
purple, red, green, yellow, pink, light_blue, dark_blue""",

            "4": """[Utility Commands]
.sessions - Check active sessions
.search <query> - Web search
.massdm <message> - Mass DM
.afk [message] - Set AFK status
.back - Remove AFK status
.phub <text> - Generate PH style image""",

            "5": """[API Features]
.extension <name> - Look up n0va.one extension
.tiktok <username> - TikTok account lookup
.script <name> - Run custom script
.ai <prompt> - Chat with AI
.aikey <key> - Set OpenAI key

Auto Features:
• Status Rotation
• Custom Header/Footer
• AFK System with Notifications
• Session Detection"""
        }

        args = message.content.split()
        if len(args) == 3 and args[1].lower() == "page":
            page = args[2]
        else:
            page = "1"

        if page in pages:
            msg = await message.channel.send(create_message(f"{pages[page]}\n\nPage {page}/5 - Use .cmds page <1-5>"))
        else:
            msg = await message.channel.send(create_message("Invalid page number. Use .cmds page <1-5>"))
        
        await asyncio.sleep(config['message_timer'])
        await msg.delete()

    elif message.content.startswith('.phub'):
        await message.delete()
        text = message.content[6:].strip()
        if text:
            try:
                # Create PH style image
                img = Image.new('RGB', (500, 100), color='black')
                d = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial.ttf", 60)
                d.text((10,10), text, font=font, fill='orange')
                
                # Save and send
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                await message.channel.send(file=discord.File(buffer, 'phub.png'))
            except:
                pass

    elif message.content.startswith('.extension'):
        await message.delete()
        ext = message.content[11:].strip()
        if ext:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                url = f'https://n0va.one/{ext}'
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as r:
                        if r.status == 404:
                            msg = await message.channel.send(create_message(f"✅ Extension '{ext}' is available!"))
                        else:
                            msg = await message.channel.send(create_message(f"❌ Extension '{ext}' is taken."))
                await asyncio.sleep(config['message_timer'])
                await msg.delete()
            except Exception as e:
                print(f"Extension error: {e}")

    elif message.content.startswith('.tiktok'):
        await message.delete()
        username = message.content[8:].strip()
        if username:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                url = f'https://www.tiktok.com/@{username}'
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as r:
                        if r.status == 200:
                            html = await r.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract stats from meta tags
                            stats = {
                                'Followers': '0',
                                'Following': '0',
                                'Likes': '0'
                            }
                            
                            meta_tags = soup.find_all('meta', {'property': True})
                            for tag in meta_tags:
                                if 'followers' in tag.get('property', '').lower():
                                    stats['Followers'] = tag.get('content', '0')
                                elif 'following' in tag.get('property', '').lower():
                                    stats['Following'] = tag.get('content', '0')
                                elif 'likes' in tag.get('property', '').lower():
                                    stats['Likes'] = tag.get('content', '0')
                            
                            content = f"TikTok Stats for @{username}\n"
                            content += f"Followers: {stats['Followers']}\n"
                            content += f"Following: {stats['Following']}\n"
                            content += f"Likes: {stats['Likes']}\n"
                            content += f"Profile: {url}"
                            
                            msg = await message.channel.send(create_message(content))
                        else:
                            msg = await message.channel.send(create_message(f"❌ TikTok user '@{username}' not found"))
                await asyncio.sleep(config['message_timer'])
                await msg.delete()
            except Exception as e:
                if not config['hide']['errors']:
                    print(f"TikTok error: {e}")

    elif message.content.startswith('.script'):
        await message.delete()
        script_name = message.content[8:].strip()
        if script_name:
            script = load_script(script_name)
            if script:
                try:
                    # Create a safe locals dict
                    locals_dict = {
                        'message': message,
                        'client': client,
                        'discord': discord,
                        'asyncio': asyncio
                    }
                    # Execute the script
                    exec(script, globals(), locals_dict)
                    # Run the script if it has a run function
                    if 'run' in locals_dict:
                        await locals_dict['run'](message, client)
                    msg = await message.channel.send(create_message(f"✅ Executed script: {script_name}"))
                except Exception as e:
                    msg = await message.channel.send(create_message(f"❌ Script error: {str(e)}"))
                await asyncio.sleep(config['message_timer'])
                await msg.delete()
            else:
                msg = await message.channel.send(create_message(f"❌ Script not found: {script_name}"))
                await asyncio.sleep(config['message_timer'])
                await msg.delete()

    elif message.content.startswith('.ai'):
        await message.delete()
        if not config['ai']['openai_key']:
            msg = await message.channel.send(create_message("❌ Please set your OpenAI key with .aikey <key>"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()
            return

        prompt = message.content[4:].strip()
        if prompt:
            try:
                headers = {
                    'Authorization': f"Bearer {config['ai']['openai_key']}",
                    'Content-Type': 'application/json'
                }
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post('https://api.openai.com/v1/chat/completions', 
                                          headers=headers, json=data) as resp:
                        if resp.status == 200:
                            response = await resp.json()
                            ai_response = response['choices'][0]['message']['content']
                            msg = await message.channel.send(create_message(f"🤖 AI Response:\n{ai_response}"))
                        else:
                            msg = await message.channel.send(create_message("❌ Failed to get AI response"))
                await asyncio.sleep(config['message_timer'])
                await msg.delete()
            except Exception as e:
                msg = await message.channel.send(create_message(f"❌ AI Error: {str(e)}"))
                await asyncio.sleep(config['message_timer'])
                await msg.delete()

    elif message.content.startswith('.aikey'):
        await message.delete()
        key = message.content[7:].strip()
        if key:
            config['ai']['openai_key'] = key
            save_config()
            msg = await message.channel.send(create_message("OpenAI key updated!"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content == '.online':
        await message.delete()
        url = "https://discord.com/api/v9/users/@me/settings"
        headers = {
            'Authorization': client.http.token,
            'Content-Type': 'application/json'
        }
        data = {"status": "online"}
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=data, headers=headers) as resp:
                if resp.status == 200:
                    msg = await message.channel.send(create_message("Status set to: 🟢 Online ✨"))
                    await asyncio.sleep(config['message_timer'])
                    await msg.delete()

    elif message.content == '.idle':
        await message.delete()
        url = "https://discord.com/api/v9/users/@me/settings"
        headers = {
            'Authorization': client.http.token,
            'Content-Type': 'application/json'
        }
        data = {"status": "idle"}
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=data, headers=headers) as resp:
                if resp.status == 200:
                    msg = await message.channel.send(create_message("Status set to: 🌙 Idle 💫"))
                    await asyncio.sleep(config['message_timer'])
                    await msg.delete()

    elif message.content == '.dnd':
        await message.delete()
        url = "https://discord.com/api/v9/users/@me/settings"
        headers = {
            'Authorization': client.http.token,
            'Content-Type': 'application/json'
        }
        data = {"status": "dnd"}
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=data, headers=headers) as resp:
                if resp.status == 200:
                    msg = await message.channel.send(create_message("Status set to: ⛔ Do Not Disturb 🔥"))
                    await asyncio.sleep(config['message_timer'])
                    await msg.delete()

    elif message.content.startswith('.setstatus'):
        await message.delete()
        new_status = message.content[10:].strip()
        if new_status:
            # Add a default emoji if none provided
            if not any(c in new_status for c in ['🌟', '🔥', '❓', '👑', '💥', '🙏', '✨', '🌎', '💫', '🚀', '💯', '⚡', '🎮', '🎯', '💪']):
                new_status = f"✨ {new_status}"
            custom_status_messages.append(new_status)
            status_manager.add_status(new_status)  # Add to status manager too
            msg = await message.channel.send(create_message(f"Added new status: {new_status} 🌟"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content == '.liststatus':
        await message.delete()
        status_list = "\n".join(f"{i+1}. {status}" for i, status in enumerate(custom_status_messages))
        msg = await message.channel.send(create_message(f"Current Status Messages:\n{status_list}"))
        await asyncio.sleep(config['message_timer'])
        await msg.delete()

    elif message.content.startswith('.delstatus'):
        await message.delete()
        try:
            index = int(message.content[10:].strip()) - 1
            if 0 <= index < len(custom_status_messages):
                removed = custom_status_messages.pop(index)
                status_manager.status_messages.pop(index)  # Remove from status manager too
                msg = await message.channel.send(create_message(f"Removed status: {removed}"))
            else:
                msg = await message.channel.send(create_message("Invalid status index"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()
        except:
            pass

    elif message.content.startswith('.timer'):
        await message.delete()
        try:
            new_time = int(message.content[7:].strip())
            if 1 <= new_time <= 300:  # Limit between 1 and 300 seconds
                config['message_timer'] = new_time
                save_config()
                msg = await message.channel.send(create_message(f"Message deletion timer set to {new_time} seconds ⏱️"))
            else:
                msg = await message.channel.send(create_message("Please specify a time between 1 and 300 seconds ⚠️"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()
        except ValueError:
            msg = await message.channel.send(create_message("Please specify a valid number of seconds ⚠️"))
            await asyncio.sleep(config['message_timer'])
            await msg.delete()

    elif message.content == "clear":
        os.system('cls' if os.name == 'nt' else 'clear')
        ascii_art = pyfiglet.figlet_format("n0va selfbot")
        print(f"{Fore.MAGENTA}{ascii_art}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Connected as: {client.user}{Style.RESET_ALL}")

    elif cmd == "scripts":
        if not os.path.exists('scripts'):
            os.makedirs('scripts')
        scripts = [f[:-3] for f in os.listdir('scripts') if f.endswith('.py')]
        if scripts:
            print(f"\n{Fore.GREEN}Available scripts:{Style.RESET_ALL}")
            for script in scripts:
                print(f"- {script}")
        else:
            print(f"{Fore.YELLOW}No scripts found in scripts folder{Style.RESET_ALL}")

def create_message(content):
    header_color = colors.get(config['header']['color'], "35")
    footer_color = colors.get(config['footer']['color'], "35")
    return f"""```ansi
\u001b[{header_color}m{config['header']['text']}\u001b[0m

{content}

\u001b[{footer_color}m{config['footer']['text']}\u001b[0m
```"""

def show_console():
    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

def hide_console():
    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

# Start terminal commands in a separate thread
import threading
threading.Thread(target=terminal_commands, daemon=True).start()

# Install required package:
# pip install discord.py-self

def load_script(script_name):
    try:
        script_path = os.path.join('scripts', f'{script_name}.py')
        if not os.path.exists('scripts'):
            os.makedirs('scripts')
        if os.path.exists(script_path):
            with open(script_path, 'r') as f:
                return f.read()
        return None
    except Exception as e:
        print(f"Script loading error: {e}")
        return None

# Update main function
async def main():
    try:
        if not os.path.exists('config.json'):
            print("Creating default config...")
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=4)
        
        # Load token from config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        if not config.get('token'):
            token = input("Please enter your Discord token: ").strip()
            if not token:
                print("Token cannot be empty!")
                return
            config['token'] = token
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
        
        print("Starting selfbot...")
        await client.start(config['token'])  # Removed bot=False parameter
            
    except Exception as e:
        print(f"Failed to start: {str(e)}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Start terminal commands in the main thread
        terminal_commands()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        input("Press Enter to exit...")

# Add this function
async def shutdown():
    try:
        print("Shutting down...")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        await client.close()
    except Exception as e:
        print(f"Error during shutdown: {e}")
    finally:
        asyncio.get_event_loop().stop()

