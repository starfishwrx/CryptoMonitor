#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
加密货币轧空监控机器人启动脚本
用于定期运行监控程序，捕捉潜在的山寨币轧空机会
"""

import time
import logging
from datetime import datetime
import sys
import os

# 尝试导入schedule
try:
    import schedule
except ImportError:
    print("\n正在安装schedule模块...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "schedule"])
    import schedule

# 确保crypto_monitor可以被导入
try:
    from crypto_monitor import CryptoMonitor
except ImportError:
    # 如果在当前目录下找不到，尝试添加目录到系统路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    from crypto_monitor import CryptoMonitor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("monitor_scheduler.log")
    ]
)
logger = logging.getLogger(__name__)

def run_monitor_job():
    """运行监控任务"""
    logger.info(f"开始监控任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        # 使用新的数据目录
        monitor = CryptoMonitor(data_dir="data_new")
        
        # 记录监控开始
        monitor_logger = logging.getLogger('monitor')
        monitor_logger.info(f"========== 监控会话开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==========")
        monitor_logger.info(f"监控参数: 资金费率阈值 = 0.001 (0.1%), OI增长比例阈值 = 2.0")
        
        # 收集数据
        logger.info("开始收集数据...")
        data = monitor.collect_data()
        
        # 记录收集到的交易对数量
        if data:
            monitor_logger.info(f"成功收集了 {len(data)} 个交易对的数据")
            
            # 记录极端资金费率的交易对
            extreme_funding = [item for item in data if abs(item['last_funding_rate']) > 0.001]
            if extreme_funding:
                monitor_logger.info(f"发现 {len(extreme_funding)} 个极端资金费率的交易对:")
                for item in sorted(extreme_funding, key=lambda x: abs(x['last_funding_rate']), reverse=True)[:10]:  # 只显示前10个
                    monitor_logger.info(f"  {item['symbol']}: 资金费率 = {item['last_funding_rate']:.4%}, 标记价格 = {item['mark_price']:.4f}, 基差 = {item['basis_percent']:.2f}%")
        else:
            monitor_logger.info("没有收集到数据，请检查网络连接和API状态")
        
        # 分析OI变化
        _, significant_oi_changes = monitor.analyze_oi_changes(data)
        
        # 记录显著的OI变化
        if significant_oi_changes:
            monitor_logger.info(f"\n发现 {len(significant_oi_changes)} 个显著的OI变化:")
            for item in significant_oi_changes[:10]:  # 只显示前10个
                monitor_logger.info(f"  {item['symbol']}: OI增长比例 = {item['oi_ratio']:.2f}x, 资金费率 = {item['funding_rate']:.4%}, 标记价格 = {item['mark_price']:.4f}")
        
        # 检测异常信号
        logger.info("检测异常信号...")
        anomalies = monitor.detect_anomalies(data)
        
        if anomalies:
            monitor_logger.info(f"❗ 检测到 {len(anomalies)} 个潜在轧空信号 ❗")
            for anomaly in anomalies:
                monitor_logger.info(f"潜在轧空信号: {anomaly['symbol']}, 资金费率: {anomaly['funding_rate']:.4%}, OI增长: {anomaly['oi_ratio']:.2f}x, 标记价格: {anomaly['mark_price']:.4f}")
                logger.info(f"潜在轧空信号: {anomaly['symbol']}, 资金费率: {anomaly['funding_rate']:.4%}, OI增长: {anomaly['oi_ratio']:.2f}x")
        else:
            monitor_logger.info("本次监控未检测到异常信号")
            logger.info("未检测到异常信号")
        
        # 发送汇总信息到Telegram
        # 检查是否有异常费率的交易对
        extreme_funding = [item for item in data if abs(item['last_funding_rate']) > 0.001]
        
        # 当有异常费率、OI显著变化或异常信号时发送通知
        if extreme_funding or significant_oi_changes or anomalies:
            try:
                # 构建消息
                message = f"📊 监控汇总报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # 添加异常费率信息
                extreme_funding = [item for item in data if abs(item['last_funding_rate']) > 0.001]
                if extreme_funding:
                    message += f"\n\n🔴 异常费率交易对 ({len(extreme_funding)})个):\n"
                    for item in sorted(extreme_funding, key=lambda x: abs(x['last_funding_rate']), reverse=True)[:10]:
                        message += f"  • {item['symbol']}: {item['last_funding_rate']:.4%}\n"
                    message += "\n"
                
                # 添加OI增长信息
                if significant_oi_changes:
                    message += f"📈 OI显著增长交易对 ({len(significant_oi_changes)})个):\n"
                    for item in sorted(significant_oi_changes, key=lambda x: x['oi_ratio'], reverse=True)[:10]:
                        message += f"  • {item['symbol']}: {item['oi_ratio']:.2f}x\n"
                    message += "\n"
                
                # 添加异常信号信息
                if anomalies:
                    message += f"⚠️ 潜在轧空信号 ({len(anomalies)})个):\n"
                    for anomaly in anomalies:
                        message += f"  • {anomaly['symbol']}: 费率={anomaly['funding_rate']:.4%}, OI={anomaly['oi_ratio']:.2f}x\n"
                
                # 发送消息
                from crypto_monitor import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
                if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                    payload = {
                        'chat_id': TELEGRAM_CHAT_ID,
                        'text': message
                    }
                    import requests
                    requests.post(url, data=payload)
                    logger.info("已发送监控汇总报告到Telegram")
                else:
                    logger.warning("未配置Telegram Bot，跳过发送汇总报告")
            except Exception as e:
                logger.error(f"发送汇总报告时出错: {str(e)}")
        
        close_to_threshold = [item for item in data if item['oi_ratio'] > 1.7]
        if close_to_threshold:
            logger.info("\nOI增长比例接近阈值(>1.7)的交易对:")
            for item in close_to_threshold:
                logger.info(f"  {item['symbol']}: OI增长比例 = {item['oi_ratio']:.2f}x, 资金费率 = {item['funding_rate']:.4%}, 标记价格 = {item['mark_price']:.4f}")
        
        # 记录监控结束
        monitor_logger.info(f"========== 监控会话结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==========\n")
    except Exception as e:
        logger.error(f"监控任务执行失败: {str(e)}")
    
    logger.info(f"监控任务完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("-" * 50)

def main():
    """主函数"""
    logger.info("启动加密货币轧空监控定时任务")
    logger.info("将每5分钟运行一次监控")
    
    # 立即运行一次
    run_monitor_job()
    
    # 设置定时任务，每5分钟运行一次
    schedule.every(5).minutes.do(run_monitor_job)
    
    # 持续运行定时任务
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("监控程序被用户中断")
            break
        except Exception as e:
            logger.error(f"定时任务出错: {str(e)}")
            # 短暂暂停后继续
            time.sleep(10)

if __name__ == "__main__":
    main()
