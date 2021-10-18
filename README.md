# Discord bot for new world status

用 python + discord.py 製作的查詢 New World Online 伺服器狀態的機器人，資料來源為 https://newworldstatus.com/

# 如何使用？

## API 版本

向 discord 申請一支機器人，傳送門👉 https://discord.com/developers/applications

向 New World Status 申請 API Credentials，傳送門👉 https://newworldstatus.com/__automata/gtm/request.aspx

clone 這個 repository，將 `/api/.env.example` 重新命名為 `/api/.env`
將 discord bot token 及 api key 填入 `/api/.env`，並確保 discord bot token 有 `Send Messages` 及 `Manage Messages` 兩個權限。

接著啟動程式，到 `/api` 目錄，並輸入以下指令：
```
$ python discord_bot.py
```
將 discord bot 邀進你的伺服器，或直接私訊機器人以下指令：
```
!Server [這邊放你要查詢的世界的名稱]
如：
!Server riallaro
!Server el dorado
!Server kokytos
```

其他參考：
* [Discord Developer Docs](https://discord.com/developers/docs/intro)
* [New World Status API 文件](https://newworldstatus.com/unofficial-status-api)

## 爬蟲版本
等 API 版本失效再更新