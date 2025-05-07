#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
加密货币轧空监控机器人
用于监控Binance永续合约市场的异常信号，捕捉潜在的山寨币轧空机会
"""

import os
import time
import pandas as pd
import numpy as np
import requests
import logging
import json
from datetime import datetime
import csv
import os.path
from pathlib import Path
from dotenv import load_dotenv
import sys
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("crypto_monitor.log")
    ]
)
logger = logging.getLogger(__name__)

# 添加实时监控记录文件
def setup_monitor_log():
    """\u8bbe\u7f6e\u5b9e\u65f6\u76d1\u63a7\u8bb0\u5f55"""
    monitor_logger = logging.getLogger('monitor')
    monitor_logger.setLevel(logging.INFO)
    
    # 创建目录
    Path('logs').mkdir(parents=True, exist_ok=True)
    
    # 创建基于时间的日志文件名
    log_filename = f"logs/monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 添加文件处理器
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    monitor_logger.addHandler(file_handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('\033[92m%(asctime)s - MONITOR: %(message)s\033[0m'))
    monitor_logger.addHandler(console_handler)
    
    return monitor_logger

# 创建监控日志器
monitor_logger = setup_monitor_log()

# 加载环境变量
load_dotenv()

# Telegram Bot配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Binance API基础URL
BINANCE_API_BASE = "https://fapi.binance.com"

# 创建带有重试机制的会话
def create_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    """创建一个带有重试机制的requests会话"""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

class CryptoMonitor:
    def __init__(self, data_dir="data"):
        """初始化监控器"""
        self.data_dir = data_dir
        # 创建数据目录
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        # 创建带有重试机制的会话
        self.session = create_retry_session(retries=5, backoff_factor=0.5)
        logger.info(f"初始化加密货币监控器，数据将保存在 {data_dir} 目录")
    
    def get_usdt_perpetual_symbols(self):
        """获取所有USDT永续合约交易对"""
        try:
            url = f"{BINANCE_API_BASE}/fapi/v1/exchangeInfo"
            # 使用会话发送请求
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            # 筛选USDT永续合约
            symbols = [symbol['symbol'] for symbol in data['symbols'] 
                      if symbol['quoteAsset'] == 'USDT' and symbol['contractType'] == 'PERPETUAL']
            
            logger.info(f"获取到 {len(symbols)} 个USDT永续合约交易对")
            return symbols
        except Exception as e:
            logger.error(f"获取交易对失败: {str(e)}")
            return []
    
    def get_funding_rate(self, symbol):
        """获取资金费率"""
        try:
            # 添加随机延迟，避免API限流
            time.sleep(0.01)  # 10毫秒延迟
            
            url = f"{BINANCE_API_BASE}/fapi/v1/premiumIndex"
            params = {'symbol': symbol}
            # 使用会话发送请求
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            # 提取资金费率
            funding_rate = float(data.get('lastFundingRate', 0))
            mark_price = float(data.get('markPrice', 0))
            index_price = float(data.get('indexPrice', 0))
            
            # 计算基差和基差百分比
            basis = mark_price - index_price
            basis_percent = (basis / index_price) * 100 if index_price else 0
            
            # 获取当前时间戳，以ISO格式存储，便于CSV处理和排序
            current_time = datetime.now()
            timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
            timestamp_ms = int(current_time.timestamp() * 1000)  # 毫秒级时间戳
            
            return {
                'symbol': symbol,
                'mark_price': mark_price,
                'index_price': index_price,
                'basis': basis,
                'basis_percent': basis_percent,
                'last_funding_rate': funding_rate,
                'timestamp': timestamp_str,
                'timestamp_ms': timestamp_ms
            }
        except Exception as e:
            logger.error(f"获取{symbol}资金费率失败: {str(e)}")
            return None
    
    def get_open_interest(self, symbol):
        """获取持仓量数据"""
        try:
            # 添加随机延迟，避免API限流
            time.sleep(0.01)  # 10毫秒延迟
            
            url = f"{BINANCE_API_BASE}/fapi/v1/openInterest"
            params = {'symbol': symbol}
            # 使用会话发送请求
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            # 提取持仓量
            oi = float(data.get('openInterest', 0))
            
            return oi
        except Exception as e:
            logger.error(f"获取{symbol}持仓量失败: {str(e)}")
            return 0
    
    def get_long_short_ratio(self, symbol):
        """获取多空比数据"""
        try:
            # 添加随机延迟，避免API限流
            time.sleep(0.01)  # 10毫秒延迟
            
            # 获取账户多空比
            url = f"https://fapi.binance.com/futures/data/topLongShortAccountRatio"
            params = {
                'symbol': symbol,
                'period': '5m',  # 5分钟周期
                'limit': 1  # 只获取最新的一条数据
            }
            # 使用会话发送请求
            response = self.session.get(url, params=params, timeout=10)
            account_data = response.json()
            
            if not account_data or len(account_data) == 0:
                return {
                    'long_short_ratio': 1.0,  # 默认值，表示多空持平
                    'long_account': 50,
                    'short_account': 50
                }
            
            # 提取数据
            latest = account_data[0]
            long_short_ratio = float(latest.get('longShortRatio', 1.0))
            long_account = float(latest.get('longAccount', 50))
            short_account = float(latest.get('shortAccount', 50))
            
            return {
                'long_short_ratio': long_short_ratio,
                'long_account': long_account,
                'short_account': short_account
            }
        except Exception as e:
            logger.error(f"获取{symbol}多空比数据失败: {str(e)}")
            return {
                'long_short_account_ratio': 1.0,
                'top_trader_account_ls_ratio': 1.0,
                'top_trader_position_ls_ratio': 1.0,
                'taker_buy_sell_ratio': 1.0
            }
    
    def collect_data(self):
        """收集所有交易对的数据"""
        symbols = self.get_usdt_perpetual_symbols()
        all_data = []
        
        for symbol in symbols:
            try:
                # 获取资金费率数据
                funding_data = self.get_funding_rate(symbol)
                if not funding_data:
                    continue
                
                # 获取持仓量
                oi = self.get_open_interest(symbol)
                funding_data['oi'] = oi
                
                # 获取多空比数据
                ls_data = self.get_long_short_ratio(symbol)
                funding_data.update(ls_data)
                
                all_data.append(funding_data)
                
                # 将数据保存到CSV文件
                self.save_data_to_csv(funding_data)
                
                # 避免API请求过于频繁
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"处理{symbol}数据时出错: {str(e)}")
        
        return all_data
    
    def save_data_to_csv(self, data):
        """将数据保存到CSV文件"""
        symbol = data['symbol']
        file_path = os.path.join(self.data_dir, f"{symbol}.csv")
        file_exists = os.path.isfile(file_path)
        
        try:
            with open(file_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)
        except Exception as e:
            logger.error(f"保存{symbol}数据到CSV失败: {str(e)}")
    
    def analyze_oi_changes(self, data):
        """分析持仓量变化"""
        oi_analysis_results = []
        significant_oi_changes = []
        
        for symbol_data in data:
            symbol = symbol_data['symbol']
            
            # 检查是否有足够的历史数据进行分析
            csv_path = os.path.join(self.data_dir, f"{symbol}.csv")
            if not os.path.exists(csv_path):
                continue
            
            try:
                # 读取历史数据，使用更健壮的方式处理CSV格式变化
                # 使用on_bad_lines='skip'跳过格式不匹配的行
                df = pd.read_csv(csv_path, on_bad_lines='skip')
                
                # 确保'oi'列存在
                if 'oi' not in df.columns:
                    logger.warning(f"{symbol}数据中缺少'oi'列，跳过分析")
                    continue
                    
                if len(df) < 10:  # 确保有足够的数据点
                    continue
                
                # 计算OI变化
                recent_oi_avg = df['oi'].tail(3).mean()
                past_oi_avg = df['oi'].tail(10).mean()
                oi_ratio = recent_oi_avg / past_oi_avg if past_oi_avg > 0 else 1.0
                
                # 记录OI分析结果
                analysis_result = {
                    'symbol': symbol,
                    'oi_current': symbol_data['oi'],
                    'oi_recent_avg': recent_oi_avg,
                    'oi_past_avg': past_oi_avg,
                    'oi_ratio': oi_ratio,
                    'funding_rate': symbol_data['last_funding_rate'],
                    'mark_price': symbol_data['mark_price']
                }
                oi_analysis_results.append(analysis_result)
                
                # 记录显著的OI变化
                if oi_ratio > 2.0:  # 如果OI增长超过100%（短期激增）
                    significant_oi_changes.append(analysis_result)
                    
            except Exception as e:
                logger.error(f"分析{symbol}数据时出错: {str(e)}")
        
        # 按OI增长比例降序排序
        significant_oi_changes.sort(key=lambda x: x['oi_ratio'], reverse=True)
        
        return oi_analysis_results, significant_oi_changes
    
    def detect_anomalies(self, data, funding_threshold=0.001, oi_ratio_threshold=2.0):
        """检测异常信号
        
        触发条件：
        - 当资金费率绝对值 > 0.1%（即last_funding_rate < -0.001 或 > 0.001），且
        - 最近3次的OI均值 / 最近10次的 OI均值 > 2（OI短期激增）
        """
        anomalies = []
        
        # 先进行OI分析
        _, significant_oi_changes = self.analyze_oi_changes(data)
        
        # 记录显著的OI变化
        if significant_oi_changes:
            monitor_logger.info(f"\n发现 {len(significant_oi_changes)} 个显著的OI变化:")
            for item in significant_oi_changes[:10]:  # 只显示前10个
                monitor_logger.info(f"  {item['symbol']}: OI增长比例 = {item['oi_ratio']:.2f}x, 资金费率 = {item['funding_rate']:.4%}, 标记价格 = {item['mark_price']:.4f}")
        
        for symbol_data in data:
            symbol = symbol_data['symbol']
            funding_rate = symbol_data['last_funding_rate']
            
            # 检查是否有足够的历史数据进行分析
            csv_path = os.path.join(self.data_dir, f"{symbol}.csv")
            if not os.path.exists(csv_path):
                continue
            
            try:
                # 读取历史数据，使用更健壮的方式
                df = pd.read_csv(csv_path, on_bad_lines='skip')
                
                # 确保'oi'列存在
                if 'oi' not in df.columns:
                    logger.warning(f"{symbol}数据中缺少'oi'列，跳过分析")
                    continue
                    
                if len(df) < 10:  # 确保有足够的数据点
                    continue
                
                # 计算OI变化
                recent_oi_avg = df['oi'].tail(3).mean()  # 最近3次的OI均值
                past_oi_avg = df['oi'].tail(10).mean()   # 最近10次的OI均值
                oi_ratio = recent_oi_avg / past_oi_avg if past_oi_avg > 0 else 1.0
                
                # 检测异常 - 根据触发条件进行判断
                # 1. 资金费率绝对值 > 0.1%
                # 2. OI短期激增（最近3次均值/最近10次均值 > 2）
                if (abs(funding_rate) > funding_threshold) and (oi_ratio > oi_ratio_threshold):
                    # 创建异常信号记录
                    anomaly = {
                        'symbol': symbol,
                        'funding_rate': funding_rate,
                        'oi_ratio': oi_ratio,
                        'mark_price': symbol_data['mark_price'],
                        'basis_percent': symbol_data['basis_percent'],
                        'long_short_ratio': symbol_data.get('long_short_ratio', 1.0)  # 使用新的字段名
                    }
                    anomalies.append(anomaly)
                    
                    # 发送警报
                    self.send_alert(anomaly)
            except Exception as e:
                logger.error(f"分析{symbol}数据时出错: {str(e)}")
        
        return anomalies
    
    def send_alert(self, anomaly):
        """通过Telegram发送警报"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("未配置Telegram Bot，跳过发送警报")
            return
        
        try:
            symbol = anomaly['symbol']
            funding_rate = anomaly['funding_rate']
            oi_ratio = anomaly['oi_ratio']
            mark_price = anomaly['mark_price']
            basis_percent = anomaly['basis_percent']
            ls_ratio = anomaly['long_short_ratio']
            
            # 构建消息
            message = f"🚨 潜在轧空信号 🚨\n\n"
            message += f"交易对: {symbol}\n"
            message += f"资金费率: {funding_rate:.4%}\n"
            message += f"OI增长比例: {oi_ratio:.2f}x\n"
            message += f"标记价格: {mark_price:.4f}\n"
            message += f"基差百分比: {basis_percent:.2f}%\n"
            message += f"多空比: {ls_ratio:.2f}\n\n"
            message += f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # 发送消息
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message
                # 移除Markdown格式，避免格式错误
                # 'parse_mode': 'Markdown'
            }
            
            # 添加调试信息
            logger.info(f"正在发送Telegram消息到chat_id: {TELEGRAM_CHAT_ID}")
            logger.info(f"使用的Bot Token: {TELEGRAM_BOT_TOKEN[:5]}...{TELEGRAM_BOT_TOKEN[-5:] if TELEGRAM_BOT_TOKEN else ''}")
            
            response = requests.post(url, data=payload)
            response_json = response.json()
            
            if response.status_code == 200 and response_json.get('ok'):
                logger.info(f"成功发送{symbol}轧空信号警报")
            else:
                logger.error(f"发送警报失败: 状态码 {response.status_code}, 响应: {response.text}")
                # 检查是否有错误描述
                if 'description' in response_json:
                    logger.error(f"错误描述: {response_json['description']}")
        except Exception as e:
            logger.error(f"发送警报时出错: {str(e)}")
            # 添加更详细的错误信息
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            
            # 尝试验证Telegram Bot Token
            try:
                verify_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
                verify_response = requests.get(verify_url)
                logger.info(f"Bot验证结果: {verify_response.text}")
            except Exception as verify_error:
                logger.error(f"验证Bot Token时出错: {str(verify_error)}")


def main():
    """主函数"""
    monitor = CryptoMonitor()
    
    # 记录监控开始
    monitor_logger.info(f"========== 监控会话开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==========")
    monitor_logger.info(f"监控参数: 资金费率阈值 = 0.001 (0.1%), OI增长比例阈值 = 2.0")
    
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
    
    logger.info("检测异常信号...")
    
    # 分析OI变化
    _, significant_oi_changes = monitor.analyze_oi_changes(data)
    
    # 检测异常信号
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
                message += f"🔴 异常费率交易对 ({len(extreme_funding)})个:\n"
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
    
        # 记录监控结束
    monitor_logger.info(f"========== 监控会话结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==========\n")

if __name__ == "__main__":
    main()
