# from rich import print
import discord
from discord import app_commands
from discord.ext import commands
from _cog_class import cog_class
from typing import Literal,Optional
import utils.save_data as svae_data

class order(cog_class):
    def __init__(self, bot):
        super().__init__(bot)
        print("order load")
        self.restaurants = svae_data.get_data('restaurants.json')
        self.dishes = self.restaurants.get("dishes",[])
        print(self.dishes)

    def creat_view_for_modify_order(self):
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="1",
                style=discord.ButtonStyle.blurple,
                custom_id="2"
            )
        )
        view.add_item(
            discord.ui.Select(custom_id="3", placeholder="選擇要點啥", options=
                [discord.SelectOption(label=D['name'],value=D['name'],description=D.get('description','')) for D in self.dishes + [{'name':'其他'}]]
            )
        )

        return view    

    @app_commands.command(name="order", description="訂餐")
    # @app_commands.describe(dish ='點啥?',price='價錢?')
    async def order(self,interaction: discord.Interaction):
        view = self.creat_view_for_modify_order()
        # await interaction.response.send_message(f"您選擇了菜品 {dish}，價格 {price}")
        self.bot.dispatch("what","ss")
        await interaction.response.send_message(content="測試", view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        IDD = interaction.data.get("custom_id") 
        print(IDD)

    @commands.Cog.listener()
    async def on_what(self,t):
        print(t)

async def setup(bot):
    await bot.add_cog(order(bot))
