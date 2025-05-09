
## 核心监控指标

1. **极端负费率**：负值过大（如<-0.1%）表明庄家对现货控盘度高
2. **持仓量(OI)激增**：OI快速上升，暗示庄家大量建仓
3. **突破阻力位**：价格突破关键点位，可能触发空头清算
4. **指标恢复正常**：空头清算后多空比上升，OI回落，费率回归正常

## 异常警报逻辑

设置触发条件，可自定义：
- 当资金费率绝对值 > 0.1%（即last_funding_rate < -0.001 或 > 0.001），且
- 最近3次的OI均值 / 最近10次的 OI均值 > 2（OI短期激增）

## 安装与配置

1. 克隆仓库并进入项目目录
2. 激活虚拟环境：
   ```
   venv\Scripts\activate
   ```
3. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
4. 配置环境变量：
   - 复制`.env.example`到`.env`
   - 在`.env`文件中添加Telegram Bot相关配置：
     ```
     TELEGRAM_BOT_TOKEN=your_telegram_bot_token
     TELEGRAM_CHAT_ID=your_telegram_chat_id
     ```

## 使用方法

### 单次运行

```bash
python tools/crypto_monitor.py
```

### 定时监控（推荐）

设置定时任务，每5分钟运行一次：

**Windows (使用任务计划程序):**
```
schtasks /create /sc minute /mo 5 /tn "CryptoMonitor" /tr "cd /d E:\Windsurf\test1\my-project && venv\Scripts\python.exe tools\crypto_monitor.py"
```

**Linux/Mac (使用crontab):**
```
*/5 * * * * cd /path/to/project && venv/bin/python tools/crypto_monitor.py
```

## 自定义参数

您可以在`crypto_monitor.py`中修改以下参数来调整监控灵敏度：

- `funding_threshold`: 资金费率阈值，默认为0.001（0.1%）
- `oi_ratio_threshold`: OI增长比例阈值，默认为2.0（最近3次平均值是最近10次平均值的2倍）

## 数据存储

所有收集的数据将保存在`data_new/`目录下，按交易对分别存储为CSV文件，便于后续分析。

## 最新功能和改进

- **改进的数据收集速度**：将API请求的延迟从0.1-0.5秒降低到10毫秒，大大加快了数据收集速度
- **统一数据目录**：定时任务和单次执行使用相同的`data_new`目录，确保数据一致性
- **增强Telegram通知功能**：当有以下情况时自动发送通知：
  - 异常费率的交易对（资金费率绝对值 > 0.1%）
  - OI显著变化的交易对（OI增长比例 > 2.0）
  - 潜在轧空信号（同时满足上述两个条件）
- **更健壮的CSV处理**：使用`on_bad_lines='skip'`参数处理格式不一致的CSV文件

## 警报示例

当检测到潜在的轧空信号时，您将收到类似以下格式的Telegram消息：

```
🚨 潜在轧空信号 🚨

交易对: VOXELUSDT
资金费率: -0.1200%
OI增长比例: 2.35x
标记价格: 0.4521
基差百分比: -0.15%
多空比: 0.78

时间: 2025-05-02 20:30:45
```

## 汇总报告

除了单个轧空信号通知外，系统还会在每次监控结束时发送汇总报告，包含：

- 异常费率交易对排行（最多10个）
- OI显著增长交易对排行（最多10个）
- 潜在轧空信号列表

## 贡献与反馈

欢迎通过以下方式贡献或提供反馈：

1. 提交Issue报告问题或提出新功能建议
2. Fork仓库并提交Pull Request
3. 分享您的使用经验和改进建议

## 免责声明

本项目仅供学习和研究使用，不构成任何投资建议。交易加密货币涉及高风险，请谨慎决策并自行承担风险。

## 注意事项

- 该工具仅提供参考信号，不构成投资建议
- 交易决策应结合其他技术分析和基本面分析

## GitHub相关信息

- 仓库地址：https://github.com/starfishwrx/crypto-squeeze-monitor
- 项目主页：https://starfishwrx.github.io/crypto-squeeze-monitor
- 问题反馈：https://github.com/starfishwrx/crypto-squeeze-monitor/issues
