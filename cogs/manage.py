# from rich import print
import discord
from discord import app_commands
from discord.ext import commands
from _cog_class import cog_class
from typing import Literal,Optional,List
import utils.save_data as svae_data


async def restaurant_autocomplete( interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=restaurant, value=restaurant)
        for restaurant in ["A","B"] if current.lower() in restaurant.lower()
    ][:25]


class manage(cog_class):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        print("manage load")

        self.restaurants = ["McDonald's", "KFC", "Subway"]

    @app_commands.command(name="creat", description="創建訂餐活動")
    @app_commands.describe(menu ='菜單圖片?',restaurant='此餐廳名稱或代號?',saved_restaurant='使用之前的紀錄?')
    # @app_commands.choices(saved_restaurant=[
    #     app_commands.Choice(name='是', value='T'),
    #     app_commands.Choice(name='否', value='F')
    # ])
    # @app_commands.autocomplete(saved_restaurant= 'restaurant_autocomplete')
    # @app_commands.autocomplete(saved_restaurant = (lambda:[app_commands.Choice(name="restaurant", value="restaurant")]))
    @app_commands.autocomplete(saved_restaurant = restaurant_autocomplete)
    # @(
    #     lambda method:
    #         lambda self, *args, **kwargs:
    #             app_commands.autocomplete(saved_restaurant = self.restaurant_autocomplete)(method)(self, *args, **kwargs)
    # )       
    async def creat(self,interaction: discord.Interaction, restaurant:str = None ,menu: discord.Attachment = None , saved_restaurant:Literal['T', 'F'] = None):
        if (menu is None or restaurant is None) and saved_restaurant is None:
            await interaction.response.send_message(content="缺少資訊：創建餐廳請提供菜單，選擇歷史紀錄則可選擇更新菜單或文字",ephemeral=True)
            return 

        restaurant = saved_restaurant or restaurant
        if menu :
            with open("data/"+restaurant+".jpeg", "wb") as f:
                await menu.save(f)
            pass
        
        await interaction.response.send_message(f"創建{str(menu)},{saved_restaurant}")

    # @create.autocomplete('saved_restaurant')
    # async def restaurant_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    #     return [
    #         app_commands.Choice(name=restaurant, value=restaurant)
    #         for restaurant in self.restaurants if current.lower() in restaurant.lower()
    #     ][:25]

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
       pass


async def setup(bot):
    await bot.add_cog(manage(bot))
