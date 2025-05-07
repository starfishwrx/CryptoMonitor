# Telegram Bot 设置指南

为了让加密货币轧空监控机器人能够成功发送消息到您的Telegram，您需要完成以下设置步骤：

## 1. 创建Telegram Bot

1. 在Telegram中搜索 `@BotFather` 并开始对话
2. 发送命令 `/newbot` 来创建一个新的机器人
3. 按照BotFather的指示提供机器人名称和用户名
4. 创建成功后，BotFather会提供一个API令牌（Token），格式类似：`123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`
5. **保存这个Token**，我们将在后续步骤中使用它

## 2. 获取您的Chat ID

有两种方法可以获取您的Chat ID：

### 方法一：使用@userinfobot

1. 在Telegram中搜索 `@userinfobot` 并开始对话
2. 机器人会自动回复您的用户信息，包括您的Chat ID

### 方法二：通过API获取

1. 首先，向您的机器人发送一条消息
2. 然后访问以下URL（替换`YOUR_BOT_TOKEN`为您的Bot Token）：
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. 在返回的JSON数据中，查找 `"chat":{"id":XXXXXXXXX}` 中的数字，这就是您的Chat ID

## 3. 配置环境变量

1. 打开项目中的`.env`文件
2. 更新以下两行：
   ```
   TELEGRAM_BOT_TOKEN=您的Bot Token
   TELEGRAM_CHAT_ID=您的Chat ID
   ```

## 4. 初始化对话

**重要**：Telegram的安全策略要求用户必须先与机器人进行交互，机器人才能主动发送消息。

1. 在Telegram中搜索您创建的机器人（使用@用户名）
2. 点击"开始"或发送任何消息给机器人
3. 这一步骤是必须的，否则机器人将无法向您发送消息

## 5. 测试机器人

1. 运行以下命令测试机器人是否能成功发送消息：
   ```
   python tools/test_telegram.py
   ```

## 常见问题排查

如果您的机器人无法发送消息，请检查以下几点：

1. **Bot Token是否正确**：确保没有多余的空格或字符
2. **Chat ID是否正确**：确保使用的是数字ID，不是用户名
3. **初始化对话**：确认您已经向机器人发送过消息
4. **网络连接**：确保您的服务器/电脑可以访问Telegram API (api.telegram.org)
5. **API响应**：检查日志中的API响应，查看具体错误信息

## 参考资料

- [Telegram Bot API官方文档](https://core.telegram.org/bots/api)
- [Telegram Bot教程](https://core.telegram.org/bots/tutorial)
