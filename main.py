# -*- coding: utf-8 -*-
import discord 
from discord.ext import commands
from discord.ui import View, Button, TextInput,Select
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
intents.members = True

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

async def add_role(interaction: discord.Interaction,user,role_name):
    new_role =  discord.utils.get(interaction.guild.roles, name=role_name)
    
    if not new_role:
        new_role =  await interaction.guild.create_role(name=role_name)
    
    if new_role not in user.roles:
        await user.add_roles(new_role)

async def check_thread(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.Thread):
        thread_id = interaction.channel.id
        
    else:
        await interaction.response.send_message(content="請在點餐討論串操作",ephemeral=True)
        return None
    
    if thread_id not in all_orders:
        await interaction.response.send_message(content="此點餐活動已結束",ephemeral=True)
        return None

    return thread_id
        
# --------------------------------------------------------------------------

class SettingView(View):
    def __init__(self,interaction:discord.Interaction,thread_id,restaurant,msg = "收款按鈕",name=None):
        super().__init__()
        self.interaction = interaction
        self.restaurant = restaurant
        self.thread_id = thread_id
        self.name = str(name)
        self.this_ODM = all_orders[self.thread_id]

        
        role = interaction.guild.get_role(1281578164535164968)
        options1 = [
            discord.SelectOption(label=member.display_name, value=str(member.id))
            for member in role.members
            if not member.bot  
        ]
        
        if not options1:
            options1 = [discord.SelectOption(label="沒有可選擇的成員", value="none")]

        select1 = Select(placeholder="添加其他負責人", options=options1, custom_id="select_option")
        select1.callback = self.select_callback 
        self.add_item(select1)
        

        options2 = [
            discord.SelectOption(label=k, value= k+"$>$"+"$=$".join(v))
            for k,v in self.this_ODM.get_bill()
        ]
        # print(self.this_ODM.get_bill())
        if not options2:
            options2 = [discord.SelectOption(label="全部交錢了", value="none2")]

        self.select2 = Select(placeholder="選擇要繳錢的人", options=options2, custom_id="select_option2")
        self.select2.callback = self.select_callback2 
        self.add_item(self.select2)


        checkout_button = Button(label=msg, style=discord.ButtonStyle.primary, custom_id="checkout")
        checkout_button.callback = self.button_callback
        self.add_item(checkout_button)


        close_button = Button(label="停止接受點餐請求"if self.this_ODM.isOpen == True else "開啟接受點餐請求", style=discord.ButtonStyle.primary, custom_id="close")
        close_button.callback = self.close_button_callback
        self.add_item(close_button)


    async def button_callback(self, interaction: discord.Interaction):
        if not self.name is None and self.name != "None":
            self.this_ODM.checkout(self.name)
            await interaction.channel.send(self.name+" 已繳錢")
            await interaction.response.edit_message(content='管理介面',view=SettingView(self.interaction,self.thread_id,self.restaurant))
        else:
            await interaction.response.edit_message(content='先選擇要繳錢的人',view=SettingView(self.interaction,self.thread_id,self.restaurant))
            # await interaction.response.send_message("先選擇要繳錢的人", ephemeral=True)


    async def select_callback2(self, interaction: discord.Interaction):
        selected_value = interaction.data['values'][0]  # 獲取選擇的值
        if selected_value == "none2":
            await interaction.response.edit_message(content='管理介面',view=SettingView(self.interaction,self.thread_id,self.restaurant))
            return
        
        # selected_option = next((option for option in self.select2.options if option.value == selected_value), None)
        selected_option = selected_value.split("$>$")[0]
        dishes = selected_value.split("$>$")[1].split("$=$")
        menu = RESTAURANT_MANAGER.get_dish(self.restaurant)
        amount = sum( menu.get(x,{}).get('price',0) for x in dishes )

        await interaction.response.edit_message(content=f'{selected_option} 應繳 {amount} 元',view=SettingView(self.interaction,self.thread_id,self.restaurant,f'按此確認 {selected_option} 已繳 {amount} 元',selected_option))


    async def select_callback(self, interaction: discord.Interaction):
        selected_value = interaction.data['values'][0] 
        if selected_value == "none":
            await interaction.response.send_message("就說沒有可選擇的成員", ephemeral=True)
            return
        
        user = interaction.guild.get_member(int(selected_value))
        if not user:
            await interaction.response.send_message("找不到該使用者", ephemeral=True)
            return
            
        await add_role(interaction,user,self.this_ODM.identity_group)
        await interaction.response.send_message(f"已添加 {user.display_name }為負責人，他可以開始使用 '/manage' 命令")


    @discord.ui.button(label="產生統計列表", style=discord.ButtonStyle.primary, custom_id="list")
    async def list_button_callback(self, interaction: discord.Interaction, button: Button):
        menu = RESTAURANT_MANAGER.get_dish(self.restaurant)
        order_list =  self.this_ODM.get_list()
        order_list_text = "\n".join([ f"{b} × {a}" for a,b in order_list])

        try:
            total = sum( menu.get(str(a),{}).get('price',None)*b for a,b in order_list)
            await interaction.response.send_message(f"{order_list_text}\n共 {total} 元")
        except:
            total = sum( menu.get(str(a),{}).get('price',0)*b for a,b in order_list)
            await interaction.response.send_message(f"有餐點價錢填寫不正確，約 {total} 元以上")


    @discord.ui.button(label="產生未繳錢列表", style=discord.ButtonStyle.primary, custom_id="list_debtor")
    async def list_button_callback2(self, interaction: discord.Interaction, button: Button):
        menu = RESTAURANT_MANAGER.get_dish(self.restaurant)
        all_order_list_text =  "-----------------------\n未繳錢者：\n"+"\n".join([
            f"{k} - {', '.join([ vp+'('+str(menu.get(vp,{}).get('price','?'))+')' for vp in v])}"
            for k,v in self.this_ODM.get_bill()
        ])   
        await interaction.response.send_message(all_order_list_text)

    async def close_button_callback(self, interaction: discord.Interaction):
        if self.this_ODM.isEnd == True:
            await interaction.response.edit_message(content='管理介面',view=SettingView(self.interaction,self.thread_id,self.restaurant))
            return
        
        self.this_ODM.isOpen = not self.this_ODM.isOpen
        await interaction.response.edit_message(content='管理介面',view=SettingView(self.interaction,self.thread_id,self.restaurant))
        await interaction.channel.send("已停止接受點餐請求！" if self.this_ODM.isOpen == False else "已開使接受點餐請求！")


    @discord.ui.button(label="收回臨時身分組(務必在點餐活動完全結束後點選)", style=discord.ButtonStyle.primary, custom_id="finish")
    async def finish_button_callback(self, interaction: discord.Interaction, button: Button):
        self.this_ODM.isOpen = False
        self.this_ODM.isEnd = True
        channel = self.interaction.channel
        await interaction.response.send_message(self.this_ODM.nick_name+" 已結束", ephemeral=True)

        if isinstance(channel, discord.Thread):
            await channel.edit(name=self.this_ODM.nick_name+"--已結束")
    
        role_name = self.this_ODM.identity_group
        role =  discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            await role.delete()

class SetNumberModal(discord.ui.Modal, title = "第一次點餐請綁訂座號"):
    def __init__(self,thread_id,restaurant,dish,price,other_number = None):
        super().__init__()
        self.thread_id = thread_id
        self.restaurant = restaurant
        self.dish = dish
        self.price = price
        self.other_number = other_number

    seat_number = discord.ui.TextInput(label = "自己的座號",custom_id = "seat_number")

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user.name
        number = self.seat_number.value
        DATA.combined_data("people",{user:number})

        if self.thread_id not in all_orders:
            await interaction.response.send_message(content="此點餐活動已結束",ephemeral=True)

        all_orders[self.thread_id].add_order(number,self.dish,self.other_number)

        if self.other_number is None:
            await interaction.response.send_message(f"綁定{user}=>{str(number)}，且你點了 {self.dish} {str(self.price)} 元",ephemeral=True)
        else:
            await interaction.response.send_message(f"綁定{user}=>{str(number)}，且你幫 {self.other_number}號 點了 {self.dish} {str(self.price)} 元",ephemeral=True)
        
        menu = RESTAURANT_MANAGER.get_dish(self.restaurant)
        all_order_list_text =  "-----------------------\n點餐紀錄：\n"+"\n".join([
            f"{k} - {', '.join([ vp+'('+str(menu.get(vp,{}).get('price','?'))+')' for vp in v])}"
            for k,v in all_orders[self.thread_id].all_order_list()
        ])   
        await interaction.channel.send(all_order_list_text)

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
        img_name = f"data/{restaurant}{str(random.randint(1000, 9999))}_{menu.filename}"
        with open(img_name, "wb") as f:
            await menu.save(f)
        RESTAURANT_MANAGER.add_image(restaurant,img_name)

    await interaction.followup.send(f"你成功創建 {restaurant} 的訂餐活動，在點餐區內的討論串中使用 '/manage' 管理此次訂餐",ephemeral=True)

    image_paths = RESTAURANT_MANAGER.get_image(restaurant)
    files = [discord.File(image_path, filename=f"image{i+1}.jpg") for i, image_path in enumerate(image_paths)]
    msg =  await MAIN_CHANNEL.send(f"@everyone {interaction.user.mention} 已發起 {restaurant} 訂餐活動！請至此討論串中查看菜單以及點餐")

    rand = random.randint(100, 999)
    thread = await MAIN_CHANNEL.create_thread(name=f"{restaurant}_{rand}--訂餐活動！",message=msg)
    await thread.send(f"菜單如下，使用 '/order' 命令點餐", files=files)

    all_orders[thread.id] = ODM(restaurant,rand)
    role_name = all_orders[thread.id].identity_group
    await add_role(interaction,interaction.user,role_name)
    
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
@app_commands.describe(price="協助填寫價錢",other_number = "若幫別人代訂請填寫他的座號",advanced = "使用進階選項來修改菜單，這不會觸發點餐行動")
async def order(interaction: discord.Interaction,dish:str,price:int = None,other_number:int = None,advanced:str = None):

    thread_id = await check_thread(interaction)
    if thread_id is None:
        return

    this_ODM = all_orders[thread_id]
    restaurant = this_ODM.restaurant
    menu = RESTAURANT_MANAGER.get_dish(restaurant)

    if price is None:
        if dish not in menu:
            await interaction.response.send_message(content="第一個點此餐點請填寫價錢",ephemeral=True)
            return 
    else:
        if dish in menu:
            await interaction.channel.send(f"{interaction.user.mention} 更改 {dish} 的價錢為 {price}")
        RESTAURANT_MANAGER.add_dish(restaurant,dish,{"price":price})

    if not advanced is None:

        if advanced == "remove":
            RESTAURANT_MANAGER.remove_dish(restaurant,dish)
            await interaction.response.send_message(content=f"{interaction.user.mention} 移除了 {dish}")
            return
            
        elif advanced.startswith("rename:"):
            new_name = advanced[7:]
            RESTAURANT_MANAGER.rename_dish(restaurant,dish,new_name)
            await interaction.response.send_message(content=f"{interaction.user.mention} 更改 {dish} 為 {new_name}")
            return
        
        await interaction.response.send_message(content="你使用了進階選項，並未觸發點餐行動",ephemeral=True)
        return

    price = RESTAURANT_MANAGER.get_dish(restaurant,dish).get("price",price)
    user = interaction.user
    number = DATA.get_data("people").get(user.name,None)

    if number is None:
        await interaction.response.send_modal(SetNumberModal(thread_id,restaurant,dish,price,other_number))
    else:    
        if not this_ODM.isOpen:
            await interaction.response.send_message(content="此點餐活動已不接受點餐",ephemeral=True)
            return

        this_ODM.add_order(number,dish,other_number)
        
        if other_number is None:
            await interaction.response.send_message(content=f"你點了 {dish} {str(price)} 元",ephemeral=True)
        else:
            await interaction.response.send_message(content=f"你幫 {other_number}號 點了 {dish} {str(price)} 元",ephemeral=True)

        
        menu = RESTAURANT_MANAGER.get_dish(restaurant)
        all_order_list_text =  "點餐紀錄\n-----------------------\n"+"\n".join([
            f"{k} - {', '.join([ vp+'('+str(menu.get(vp,{}).get('price','?'))+')' for vp in v])}"
            for k,v in this_ODM.all_order_list()
        ])   
        await interaction.channel.send(all_order_list_text)

    RESTAURANT_MANAGER.save_to_file()

@order.autocomplete('dish')
async def order_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    
    if isinstance(interaction.channel, discord.Thread):
        thread_id = interaction.channel.id
        
    else:
        return [app_commands.Choice(name="請在討論串點餐", value="xx")]
        
    if thread_id not in all_orders:
        return [app_commands.Choice(name="此點餐活動已結束", value="xx")]

    restaurant = all_orders[thread_id].restaurant
    else_option = str(current.lower())[:99]
    
    menu = RESTAURANT_MANAGER.get_dish(restaurant)
    # print(menu)
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
    
    thread_id = await check_thread(interaction)
    if thread_id is None:
        return

    this_ODM = all_orders[thread_id]
    if not this_ODM.isOpen:
        await interaction.response.send_message(content="此點餐活動已不接受修改",ephemeral=True)
        return

    restaurant = this_ODM.restaurant
    this_ODM.remove_order(dish.split("$=$")[0],dish.split("$=$")[1])

    await interaction.response.send_message(content="成功移除 "+dish.split("$=$")[1],ephemeral=True)
    menu = RESTAURANT_MANAGER.get_dish(restaurant)
    all_order_list_text =  "點餐紀錄\n-----------------------\n"+"\n".join([
        f"{k} - {', '.join([ vp+'('+str(menu.get(vp,{}).get('price','?'))+')' for vp in v])}"
        for k,v in this_ODM.all_order_list()
    ]) 
    await interaction.channel.send(all_order_list_text)


@cancel.autocomplete('dish')
async def order_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    
    if isinstance(interaction.channel, discord.Thread):
        thread_id = interaction.channel.id
        
    else:
        return [app_commands.Choice(name="請在討論串操作", value="xx")]
    
    if thread_id not in all_orders:
        return [app_commands.Choice(name="點餐活動已結束", value="xx")]

    this_ODM = all_orders[thread_id]
    if not this_ODM.isOpen:
        return [app_commands.Choice(name="點餐活動已不接受修改", value="xx")]

    user = interaction.user
    number = DATA.get_data("people").get(user.name,None)

    if number is None:
        return [app_commands.Choice(name="未綁定座號(正常來說代表你還沒沒點過餐)", value="xx")]

    ordered_dish = this_ODM.get_order(number)
    # print(ordered_dish)
    options = [
        app_commands.Choice(name=f'{D["name"]} ({D["type"]})', value= D["source"] +"$=$"+ D["name"])
        for D in ordered_dish
    ][:25]
    
    return options

# --------------------------------------------------------------------------

@bot.tree.command(name = "manage", description = "管理訂餐活動，須具備特定身分組才能使用")
async def manage(interaction: discord.Interaction):
    
    thread_id = await  check_thread(interaction)
    if thread_id is None:
        return
        
    this_ODM = all_orders[thread_id]
    if not this_ODM.isOpen:
        await interaction.response.send_message(content="此點餐活動已不接受修改",ephemeral=True)
        return

    restaurant = this_ODM.restaurant
    role_name = this_ODM.identity_group
    temp_role =  discord.utils.get(interaction.guild.roles, name=role_name)
    fixed_role = interaction.guild.get_role(1281962961740501036)
    user = interaction.user

    if temp_role not in user.roles and fixed_role not in user.roles:
        await interaction.response.send_message(content="權限不足",ephemeral=True)
        return     
        
    view = SettingView(interaction,thread_id,restaurant)
    await interaction.response.send_message(content="管理介面",ephemeral=True,view=view)
    
if __name__=='__main__':
    bot.run(os.getenv("DISCORD_BOT_KEY"))
   
