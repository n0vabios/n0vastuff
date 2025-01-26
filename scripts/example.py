# Example script that can be run with .script example
import discord
import asyncio

async def run(message, client):
    msg = await message.channel.send("Running example script...")
    await asyncio.sleep(2)
    await msg.edit(content="Script completed!")
    await asyncio.sleep(2)
    await msg.delete()

print("This is a custom script!")
# Add your custom code here 