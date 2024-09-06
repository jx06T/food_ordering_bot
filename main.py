# -*- coding: utf-8 -*-
import discord 
from discord.ext import commands
from discord.ui import View, Button, Select
from discord import app_commands
from typing import Literal,Optional,List

from dotenv import load_dotenv
import os
import time

import utils.save_data as DATA
from datetime import datetime

# ------------------------------------------------------------------------------------
load_dotenv()
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix ="$", intents = intents)
channel = None
all_orders = {}

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

    global channel
    channel = bot.get_channel(int(os.getenv("MAIN_CHANNEL_ID"))) 

    await channel.send(f'訂餐機器人上線')
    await bot.tree.sync()

@commands.is_owner()
@bot.command()
async def reload(ctx):
    await bot.tree.sync()
    await ctx.send('reloaded')
    
# --------------------------------------------------------------------------
class SettingView(View):
    def __init__(self):
        super().__init__()
        
        # 按鈕
        self.add_item(Button(label="Click Me", style=discord.ButtonStyle.primary, custom_id="button_click"))
        
        # 下拉選單
        options = [
            discord.SelectOption(label="Option 1", value="option_1"),
            discord.SelectOption(label="Option 2", value="option_2"),
            discord.SelectOption(label="Option 3", value="option_3"),
        ]
        select = Select(placeholder="Choose an option...", options=options, custom_id="select_option")
        self.add_item(select)

class SetNumberModal(discord.ui.Modal, title = "第一次點餐請綁訂座號"):
    def __init__(self,restaurant,dish,price):
        super().__init__()

        self.restaurant = restaurant
        self.dish = dish
        self.price = price

    seat_number = discord.ui.TextInput(label = "座號",custom_id = "seat_number")
    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user.name
        number = self.seat_number.value
        DATA.add_data("people","number."+user,number)

        if self.restaurant not in all_orders:
            all_orders[self.restaurant] = {}
        all_orders[self.restaurant][number] = self.dish
            
        await interaction.response.send_message(f"綁定{user}=>{str(number)}，且你點了 {self.dish} {str(self.price)} 元",ephemeral=True)
# --------------------------------------------------------------------------

@bot.tree.command(name = "creat", description = "創建訂餐活動，第一次點的餐廳請附上菜單圖片")
async def creat(interaction: discord.Interaction,restaurant:str,menu:discord.Attachment = None):
    print(str(interaction.channel))
    if str(interaction.channel).endswith("--訂餐活動！"):
        await interaction.response.send_message(content="不要玩套娃",ephemeral=True)
        return 
    
    print(restaurant)
    saved_restaurants = DATA.get_data("restaurants").get("_restaurants",[])
    if restaurant not in saved_restaurants :
        if menu is None:
            await interaction.response.send_message(content="創建新的餐廳請提供菜單",ephemeral=True)
            return 
        
        DATA.add_data("restaurants","_restaurants",[restaurant])

    if menu :
        img_name = f"data/{restaurant}{str(time.time() * 10000000)[10:]}_{menu.filename}"
        with open(img_name, "wb") as f:
            await menu.save(f)
        DATA.add_data("restaurants",restaurant+".image",[img_name])

    all_orders[restaurant] = {}

    user = interaction.user
    role_name = datetime.now().strftime("%m/%d") + restaurant + "發起者"
    order_initiator =  await interaction.guild.create_role(name=role_name)
    if order_initiator not in user.roles:
        await user.add_roles(order_initiator)

    await interaction.response.send_message(f"你成功創建 {restaurant} 的訂餐活動，在討論串中使用 '/manage' 管理此次訂餐",ephemeral=True)
    
    image_paths = DATA.get_data("restaurants").get(restaurant,{}).get("image",[])
    files = [discord.File(image_path, filename=f"image{i+1}.jpg") for i, image_path in enumerate(image_paths)]

    # view = StartView()
    msg =  await channel.send(f"@everyone {user.name} 已發起 {restaurant} 訂餐活動！請至下方討論串中查看菜單以及點餐")
    thread = await interaction.channel.create_thread(name=f"{restaurant}--訂餐活動！",message=msg)
    await thread.send(f"菜單如下，使用 '/order' 命令點餐", files=files)

@creat.autocomplete('restaurant')
async def creat_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    else_option = str(current.lower())[:99]
    restaurants = DATA.get_data("restaurants").get("_restaurants",[])
    options = [
        app_commands.Choice(name=restaurant, value=restaurant)
        for restaurant in restaurants if current.lower() in restaurant.lower()
    ][:24]
    if 1 <= len(else_option) <= 100:
        options.append(app_commands.Choice(name="(新增)"+else_option, value=else_option))
        
    return options

# --------------------------------------------------------------------------
    
@bot.tree.command(name = "order", description = "點餐，若點別人點過的東西請選擇提示的選項，若是第一個點的請填入價錢")
async def order(interaction: discord.Interaction,dish:str,price:int = None):
    if not str(interaction.channel).endswith("--訂餐活動！"):
        await interaction.response.send_message(content="請在討論串點餐",ephemeral=True)
        return 
        
    restaurant =str(interaction.channel)[:-7]
    restaurants_data = DATA.get_data("restaurants")
    menu = restaurants_data.get(restaurant,{}).get("menu",{})
    if not dish in menu:
        if  price is None:
            await interaction.response.send_message(content="第一個點此餐點請填寫價錢",ephemeral=True)
            return 
        
        DATA.add_data("restaurants",restaurant+".menu",{dish:{"price":price}})

    price = price or restaurants_data.get(restaurant,{}).get("menu",{}).get(dish,{}).get("price","?")
    user = interaction.user
    number = DATA.get_data("people").get("number",{}).get(user.name,None)

    if number is None:
        await interaction.response.send_modal(SetNumberModal(restaurant,dish,price))
    else:    
        if restaurant not in all_orders:
            all_orders[restaurant] = {}

        all_orders[restaurant][number] = dish
        await interaction.response.send_message(content=f"你點了 {dish} {str(price)} 元",ephemeral=True)
 

@order.autocomplete('dish')
async def order_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    if not str(interaction.channel).endswith("--訂餐活動！"):
        return [app_commands.Choice(name="請在討論串點餐", value="xx")]
        
    restaurant =str(interaction.channel)[:-7]
    else_option = str(current.lower())[:99]
    menu = DATA.get_data("restaurants").get(restaurant,{}).get("menu",{})
    options = [
        app_commands.Choice(name=f"{key} ({value.get('price','?')})", value=key)
        for key, value in menu.items() if current.lower() in key.lower()
    ][:24]
    
    if 1 <= len(else_option) <= 100:
        options.append(app_commands.Choice(name="(新增)"+else_option, value=else_option))
        
    return options

if __name__=='__main__':
    bot.run(os.getenv("DISCORD_BOT_KEY"))
   
