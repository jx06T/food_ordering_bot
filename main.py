# -*- coding: utf-8 -*-
import discord 
from discord.ext import commands
from discord.ui import View, Button, Select
from discord import app_commands
from typing import Literal,Optional,List

from dotenv import load_dotenv
import os
import random
from datetime import datetime

import utils.save_data as DATA
from utils.restaurant_data_manager import RDM
from utils.ordering_data_manager import ODM

# ------------------------------------------------------------------------------------
load_dotenv(override=True)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix ="$", intents = intents)
MAIN_CHANNEL = None

# ------------------------------------------------------------------------------------

RESTAURANT_MANAGER =  RDM("restaurants")
all_orders : {ODM} = {}

# ------------------------------------------------------------------------------------

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # print(message.content)
    # await MAIN_CHANNEL.send(message.content)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")

    global MAIN_CHANNEL
    MAIN_CHANNEL = bot.get_channel(int(os.getenv("MAIN_CHANNEL_ID"))) 

    await MAIN_CHANNEL.send(f'訂餐機器人上線')
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
    def __init__(self,restaurant,dish,price,other_number = None):
        super().__init__()
        self.restaurant = restaurant
        self.dish = dish
        self.price = price
        self.other_number = other_number

    seat_number = discord.ui.TextInput(label = "自己的座號",custom_id = "seat_number")
    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user.name
        number = self.seat_number.value
        DATA.combined_data("people",{user:number})

        if self.restaurant not in all_orders:
            all_orders[self.restaurant] = ODM(self.restaurant)

        all_orders[self.restaurant].add_order(number,self.dish,self.other_number)

        if self.other_number is None:
            await interaction.response.send_message(f"綁定{user}=>{str(number)}，且你點了 {self.dish} {str(self.price)} 元",ephemeral=True)
        else:
            await interaction.response.send_message(f"綁定{user}=>{str(number)}，且你幫 {self.other_number}號 點了 {self.dish} {str(self.price)} 元",ephemeral=True)

# --------------------------------------------------------------------------

async def add_role(interaction: discord.Interaction,role_name):
    user = interaction.user

    new_role =  discord.utils.get(interaction.guild.roles, name=role_name)
    
    if not new_role:
        new_role =  await interaction.guild.create_role(name=role_name)
    
    if new_role not in user.roles:
        await user.add_roles(new_role)
# --------------------------------------------------------------------------

@bot.tree.command(name = "creat", description = "創建訂餐活動，第一次點的餐廳請附上菜單圖片")
@app_commands.describe( menu="上傳餐廳菜單作為附件 (新餐廳必填)")
async def creat(interaction: discord.Interaction,restaurant:str,menu:discord.Attachment = None):
    if str(interaction.channel).endswith("--訂餐活動！"):
        await interaction.response.send_message(content="不要在點餐討論串中玩套娃",ephemeral=True)
        return 
    
    saved_restaurants = RESTAURANT_MANAGER.get_restaurants()

    if restaurant not in saved_restaurants :
        if menu is None:
            await interaction.response.send_message(content="創建新的餐廳請提供菜單",ephemeral=True)
            return 
        RESTAURANT_MANAGER.add_restaurant(restaurant)

    await interaction.response.defer(ephemeral=True)

    if menu :
        img_name = f"data/{restaurant}{str(random.randint(100000, 999999))}_{menu.filename}"
        with open(img_name, "wb") as f:
            await menu.save(f)
        RESTAURANT_MANAGER.add_image(restaurant,img_name)

    all_orders[restaurant] = ODM(restaurant)

    role_name = datetime.now().strftime("%m/%d") + restaurant + "發起者"
    await add_role(interaction,role_name)

    await interaction.followup.send(f"你成功創建 {restaurant} 的訂餐活動，在點餐區內的討論串中使用 '/manage' 管理此次訂餐",ephemeral=True)
    
    image_paths = RESTAURANT_MANAGER.get_image(restaurant)
    files = [discord.File(image_path, filename=f"image{i+1}.jpg") for i, image_path in enumerate(image_paths)]

    msg =  await MAIN_CHANNEL.send(f"@everyone {interaction.user.name} 已發起 {restaurant} 訂餐活動！請至下方討論串中查看菜單以及點餐")
    thread = await MAIN_CHANNEL.create_thread(name=f"{restaurant}--訂餐活動！",message=msg)
    await thread.send(f"菜單如下，使用 '/order' 命令點餐", files=files)

    RESTAURANT_MANAGER.save_to_file()

@creat.autocomplete('restaurant')
async def creat_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    else_option = str(current.lower())[:99]
    restaurants = RESTAURANT_MANAGER.get_restaurants()
    
    options = [
        app_commands.Choice(name=restaurant, value=restaurant)
        for restaurant in restaurants if current.lower() in restaurant.lower()
    ][:24]
    
    if 1 <= len(else_option) <= 100:
        options.append(app_commands.Choice(name="(新增)"+else_option, value=else_option))
        
    return options

# --------------------------------------------------------------------------
    
@bot.tree.command(name = "order", description = "點餐，若點別人點過的東西請選擇提示的選項，若是第一個點的請填入價錢")
@app_commands.describe(price="協助填寫價錢",other_number = "若幫別人代訂請填寫他的座號")
async def order(interaction: discord.Interaction,dish:str,price:int = None,other_number:int = None):
    if not str(interaction.channel).endswith("--訂餐活動！"):
        await interaction.response.send_message(content="請在討論串點餐",ephemeral=True)
        return 
        
    restaurant = str(interaction.channel)[:-7]

    menu = RESTAURANT_MANAGER.get_dish(restaurant)
    if  price is None:
        if dish not in menu:
            await interaction.response.send_message(content="第一個點此餐點請填寫價錢",ephemeral=True)
            return 
    else:
        RESTAURANT_MANAGER.add_dish(restaurant,dish,{"price":price})

    price = RESTAURANT_MANAGER.get_dish(restaurant,dish).get("price",price)
    user = interaction.user
    number = DATA.get_data("people").get(user.name,None)

    if number is None:
        await interaction.response.send_modal(SetNumberModal(restaurant,dish,price,other_number))
    else:    
        if restaurant not in all_orders:
            all_orders[restaurant] = ODM(restaurant)

        all_orders[restaurant].add_order(number,dish,other_number)
        
        if other_number is None:
            await interaction.response.send_message(content=f"你點了 {dish} {str(price)} 元",ephemeral=True)
        else:
            await interaction.response.send_message(content=f"你幫 {other_number}號 點了 {dish} {str(price)} 元",ephemeral=True)

    RESTAURANT_MANAGER.save_to_file()

@order.autocomplete('dish')
async def order_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    if not str(interaction.channel).endswith("--訂餐活動！"):
        return [app_commands.Choice(name="請在點餐討論串點餐", value="xx")]
        
    restaurant =str(interaction.channel)[:-7]
    else_option = str(current.lower())[:99]

    menu = RESTAURANT_MANAGER.get_dish(restaurant)
    options = [
        app_commands.Choice(name=f"{key} ({value.get('price','?')})", value=key)
        for key, value in menu.items() if current.lower() in key.lower()
    ][:24]
    
    if 1 <= len(else_option) <= 100:
        options.append(app_commands.Choice(name="(新增)"+else_option, value=else_option))
        
    return options
    
# --------------------------------------------------------------------------

@bot.tree.command(name = "cancel", description = "取消點餐(包括取消別人幫你代訂的餐或你幫別人代訂的餐)")
async def cancel(interaction: discord.Interaction,dish:str):
    if not str(interaction.channel).endswith("--訂餐活動！"):
        await interaction.response.send_message(content="請在點餐討論串操作",ephemeral=True)
        return 
        
    restaurant = str(interaction.channel)[:-7]
    if restaurant not in all_orders:
        await interaction.response.send_message(content="點餐活動已結束",ephemeral=True)


@cancel.autocomplete('dish')
async def order_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    if not str(interaction.channel).endswith("--訂餐活動！"):
        return [app_commands.Choice(name="請在點餐討論串操作", value="xx")]
        
    restaurant =str(interaction.channel)[:-7]
    user = interaction.user
    number = DATA.get_data("people").get(user.name,None)

    if number is None:
        return [app_commands.Choice(name="未綁定座號(正常來說代表你還沒沒點過餐)", value="xx")]

    if restaurant not in all_orders:
        return [app_commands.Choice(name="點餐活動已結束", value="xx")]

    ordered_dish = all_orders[restaurant].get_order(number)
    options = [
        app_commands.Choice(name=f"{D.name} ({D.type})", value=D.name)
        for D in ordered_dish
    ][:25]
    
    return options

# --------------------------------------------------------------------------

# @bot.tree.command(name = "order", description = "點餐，若點別人點過的東西請選擇提示的選項，若是第一個點的請填入價錢")
# @app_commands.describe(price="協助填寫價錢",other_number = "若幫別人代訂請填寫他的座號")
# async def order(interaction: discord.Interaction,dish:str,price:int = None,other_number:int = None):
#     if not str(interaction.channel).endswith("--訂餐活動！"):
#         await interaction.response.send_message(content="請在討論串點餐",ephemeral=True)
#         return 
        
#     restaurant = str(interaction.channel)[:-7]

#     menu = RESTAURANT_MANAGER.get_dish(restaurant)
#     if  price is None:
#         if dish not in menu:
#             await interaction.response.send_message(content="第一個點此餐點請填寫價錢",ephemeral=True)
#             return 
#     else:
#         RESTAURANT_MANAGER.add_dish(restaurant,dish,{"price":price})

#     price = RESTAURANT_MANAGER.get_dish(restaurant,dish).get("price",price)
#     user = interaction.user
#     number = DATA.get_data("people").get(user.name,None)

#     if number is None:
#         await interaction.response.send_modal(SetNumberModal(restaurant,dish,price,other_number))
#     else:    
#         if restaurant not in all_orders:
#             all_orders[restaurant] = ODM(restaurant)

#         all_orders[restaurant].add_order(number,dish,other_number)
        
#         if other_number is None:
#             await interaction.response.send_message(content=f"你點了 {dish} {str(price)} 元",ephemeral=True)
#         else:
#             await interaction.response.send_message(content=f"你幫 {other_number}號 點了 {dish} {str(price)} 元",ephemeral=True)

#     RESTAURANT_MANAGER.save_to_file()

if __name__=='__main__':
    bot.run(os.getenv("DISCORD_BOT_KEY"))
   
