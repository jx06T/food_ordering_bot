# -*- coding: utf-8 -*-

import discord 
from discord.ext import commands
from dotenv import load_dotenv
import os

# ------------------------------------------------------------------------------------
load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
# intents.members = True 

bot = commands.Bot(command_prefix ="$", intents = intents)
channel = None

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # print(message.content)
    # await channel.send(message.content)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")
    print(os.getenv("MAIN_CHANNEL_ID"))
    
    global channel
    channel = bot.get_channel(int(os.getenv("MAIN_CHANNEL_ID"))) 

    await channel.send(f'訂餐機器人上線')
    await bot.load_extension("cogs.order")
    await bot.load_extension("cogs.manage")
    slash = await bot.tree.sync()

@bot.event
async def on_what(t):
    await channel.send(t)

@commands.is_owner()
@bot.command()
async def unload(ctx,extension):
    try:
        await bot.unload_extension(f"cogs.{extension}")
        await ctx.send(F'UnLoaded {extension} done.' )
    except Exception as e :
        await ctx.send(F'{extension}?' )

@commands.is_owner()
@bot.command()
async def load(ctx,extension):
    try:
        await  bot.load_extension(f"cogs.{extension}")
        await ctx.send(F'Loaded {extension} done.' )
    except Exception as e :
        await ctx.send(F'{extension}?' )
        
@commands.is_owner()
@bot.command()
async def reload(ctx,extension):
    try:
        await  bot.reload_extension(f"cogs.{extension}")
        await ctx.send(F'Reloaded {extension} done.' )
    except Exception as e :
        await ctx.send(F'{extension}?' )
    
@bot.command()
async def check_and_assign_role(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    # 檢查用戶是否有特定身分組
    target_role = discord.utils.get(ctx.guild.roles, name="目標身分組")
    if target_role in member.roles:
        # 如果用戶有目標身分組,賦予新的身分組
        new_role = discord.utils.get(ctx.guild.roles, name="新身分組")
        if new_role is not None:
            await member.add_roles(new_role)
            await ctx.send(f"{member.mention} 已被賦予 {new_role.name} 身分組!")
        else:
            await ctx.send("無法找到新身分組。")
    else:
        await ctx.send(f"{member.mention} 沒有所需的身分組。")

    
if __name__=='__main__':
    bot.run(os.getenv("DISCORD_BOT_KEY"))
   
