# discord 訂餐統計機器人
###### *version-V1.0* 
---

[邀請連結](https://discord.com/oauth2/authorize?client_id=1281228461712867432&permissions=563330326628352&response_type=code&redirect_uri=https%3A%2F%2Fdiscord.com%2Foauth2%2Fauthorize%3Fclient_id%3D1281228461712867432&integration_type=0&scope=identify+guilds+messages.read+applications.commands+applications.commands.permissions.update+role_connections.write+bot)

## 使用方法
1. 在 discord 中新建一個機器人並取得 token，方法可以參考網路文章
2. clone 本儲存庫 ( `git clone https://github.com/jx06T/food_ordering_bot.git` )
3. 新增 `.env` 文件，填入以下內容
``` env
MAIN_CHANNEL_ID = <要使用機器人的頻道 id>
FIXED_ROLE_ID = <用來管理機器人的身份組 id>
DISCORD_BOT_KEY = <機器人 token>
```
4. 安裝`requirements.txt`中的依賴


## 指令
### 創建訂餐事件 ： /creat
- restaurant 餐廳名
- menu 菜單圖片
- 會創建一個用來統計的討論串，並將餐廳加入到資料庫

### 訂餐 ： /order
- dish 餐點名稱，若欲定餐點不存在可直接輸入
- price 餐廳名
- other_number 餐廳名
- advanced 餐廳名