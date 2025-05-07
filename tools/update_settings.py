#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
更新加密货币监控机器人设置
1. 加快数据收集速度，将延迟降低到10ms
2. 确保定时任务和单次执行使用相同的数据目录
3. 每次监控完将异常费率和OI增长比例过大的交易对信息发送给Telegram机器人
"""

import os
import re
import sys

def update_delay_settings(file_path):
    """将延迟设置从0.1-0.5秒改为10毫秒"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换随机延迟为固定10毫秒
    pattern = r"time\.sleep\(random\.uniform\(0\.1, 0\.5\)\)"
    replacement = "time.sleep(0.01)  # 10毫秒延迟"
    updated_content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("[成功] 已将延迟设置更新为10毫秒")

def update_data_directory(run_monitor_path):
    """确保定时任务和单次执行使用相同的数据目录"""
    with open(run_monitor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经设置了data_dir
    if "data_dir=\"data_new\"" in content:
        print("[成功] 数据目录已设置为data_new")
        return
    
    # 替换CryptoMonitor()为CryptoMonitor(data_dir="data_new")
    pattern = r"monitor = CryptoMonitor\(\)"
    replacement = "monitor = CryptoMonitor(data_dir=\"data_new\")"
    updated_content = re.sub(pattern, replacement, content)
    
    with open(run_monitor_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("[成功] 已将数据目录设置为data_new")

def update_telegram_notification(crypto_monitor_path):
    """确保每次监控完将异常信息发送给Telegram机器人"""
    with open(crypto_monitor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查main函数中是否已经添加了Telegram通知
    if "# 发送汇总信息到Telegram" in content:
        print("[成功] Telegram通知已配置")
        return
    
    # 在main函数结束前添加Telegram通知
    pattern = r"(    # 记录监控结束\n    monitor_logger\.info\(f\"========== 监控会话结束: {datetime\.now\(\)\.strftime\('%Y-%m-%d %H:%M:%S'\)} ==========\\n\"\))"
    replacement = r"""    # 发送汇总信息到Telegram
    if significant_oi_changes or anomalies:
        try:
            # 构建消息
            message = f"📊 监控汇总报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # 添加异常费率信息
            extreme_funding = [item for item in data if abs(item['last_funding_rate']) > 0.001]
            if extreme_funding:
                message += f"🔴 异常费率交易对 ({len(extreme_funding)}个):\n"
                for item in sorted(extreme_funding, key=lambda x: abs(x['last_funding_rate']), reverse=True)[:10]:
                    message += f"  • {item['symbol']}: {item['last_funding_rate']:.4%}\n"
                message += "\n"
            
            # 添加OI增长信息
            if significant_oi_changes:
                message += f"📈 OI显著增长交易对 ({len(significant_oi_changes)}个):\n"
                for item in sorted(significant_oi_changes, key=lambda x: x['oi_ratio'], reverse=True)[:10]:
                    message += f"  • {item['symbol']}: {item['oi_ratio']:.2f}x\n"
                message += "\n"
            
            # 添加异常信号信息
            if anomalies:
                message += f"⚠️ 潜在轧空信号 ({len(anomalies)}个):\n"
                for anomaly in anomalies:
                    message += f"  • {anomaly['symbol']}: 费率={anomaly['funding_rate']:.4%}, OI={anomaly['oi_ratio']:.2f}x\n"
            
            # 发送消息
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': message
                }
                requests.post(url, data=payload)
                logger.info("已发送监控汇总报告到Telegram")
            else:
                logger.warning("未配置Telegram Bot，跳过发送汇总报告")
        except Exception as e:
            logger.error(f"发送汇总报告时出错: {str(e)}")
    
    \g<1>"""
    
    updated_content = re.sub(pattern, replacement, content)
    
    with open(crypto_monitor_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("[成功] 已添加Telegram通知功能")

def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建文件路径
    crypto_monitor_path = os.path.join(script_dir, "crypto_monitor.py")
    run_monitor_path = os.path.join(script_dir, "run_monitor.py")
    
    # 检查文件是否存在
    if not os.path.exists(crypto_monitor_path):
        print(f"❌ 文件不存在: {crypto_monitor_path}")
        return
    
    if not os.path.exists(run_monitor_path):
        print(f"❌ 文件不存在: {run_monitor_path}")
        return
    
    # 更新设置
    print("开始更新设置...")
    update_delay_settings(crypto_monitor_path)
    update_data_directory(run_monitor_path)
    update_telegram_notification(crypto_monitor_path)
    print("设置更新完成！")

if __name__ == "__main__":
    main()
