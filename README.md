# discord 訂餐統計機器人
###### *version-V1.0* 
---

[邀請連結](https://discord.com/oauth2/authorize?client_id=1281228461712867432&permissions=563330326628352&response_type=code&redirect_uri=https%3A%2F%2Fdiscord.com%2Foauth2%2Fauthorize%3Fclient_id%3D1281228461712867432&integration_type=0&scope=identify+guilds+messages.read+applications.commands+applications.commands.permissions.update+role_connections.write+bot)(此邀請連結之機器人沒有部署在任何穩定平台，機器人不一定會響應）

## 使用方法
1. 在 discord 中新建一個機器人並取得 token，方法可以參考[網路文章](https://hackmd.io/@smallshawn95/python_discord_bot_base)
2. clone 本儲存庫 ( `git clone https://github.com/jx06T/food_ordering_bot.git` )
3. 新增 `.env` 文件，填入以下內容
``` env
MAIN_CHANNEL_ID = <要使用機器人的頻道 id>
FIXED_ROLE_ID = <用來管理機器人的身份組 id>
DISCORD_BOT_KEY = <機器人 token>
```
4. 安裝`requirements.txt`中的依賴
5. 生成邀請連結，勾選以下權限
6. 邀請機器人到伺服器後完成 .ven 檔案的配置，並設定伺服器中對該機器人的使用限制

## 指令
### 創建訂餐活動 ： /creat
- restaurant 餐廳名
- menu 菜單圖片
- 會創建一個用來統計的討論串，並將餐廳加入到資料庫

> 此指令在主頻道使用，其餘指令在點餐討論串中使用

### 訂餐 ： /order
- dish 餐點名稱，若欲定餐點不存在可直接輸入，會顯示「（新增）」直接點擊即可
- price 價錢，若為新增的餐點請務必填寫
- other_number 若幫別人代訂則在此格填入對方座號
- advanced 進階選項，填寫 dish 參數後可以修改該餐點
    - 修改價錢：在 price 選項填入更改後價錢，並在此參數填入任意內容
    - 修改名稱：此參數輸入 `rename:` + <修改後名稱>
    - 刪除：此參數輸入 `remove`
 

### 取消訂餐 /cancel






