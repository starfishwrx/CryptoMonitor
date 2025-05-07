#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试OI分析功能，查看为什么没有OI相关的报警
"""

import os
import pandas as pd
import logging
from crypto_monitor import CryptoMonitor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_oi_analysis():
    """调试OI分析功能"""
    # 使用新的数据目录
    data_dir = "data_new"
    monitor = CryptoMonitor(data_dir=data_dir)
    
    # 1. 检查数据目录中的CSV文件
    logger.info(f"检查数据目录: {data_dir}")
    if not os.path.exists(data_dir):
        logger.error(f"数据目录 {data_dir} 不存在!")
        return
    
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    logger.info(f"找到 {len(csv_files)} 个CSV文件")
    
    if not csv_files:
        logger.error("没有找到CSV文件，无法进行OI分析")
        return
    
    # 2. 检查几个CSV文件的内容
    sample_files = csv_files[:5]  # 取前5个文件作为样本
    logger.info(f"检查样本文件: {sample_files}")
    
    for csv_file in sample_files:
        file_path = os.path.join(data_dir, csv_file)
        try:
            df = pd.read_csv(file_path, on_bad_lines='skip')
            
            # 检查'oi'列是否存在
            if 'oi' not in df.columns:
                logger.warning(f"{csv_file} 中缺少'oi'列")
                continue
            
            # 检查数据点数量
            row_count = len(df)
            logger.info(f"{csv_file} 包含 {row_count} 行数据")
            
            if row_count < 10:
                logger.warning(f"{csv_file} 数据点不足10个，无法进行OI分析")
                continue
            
            # 计算OI变化
            recent_oi_avg = df['oi'].tail(3).mean()
            past_oi_avg = df['oi'].tail(10).mean()
            oi_ratio = recent_oi_avg / past_oi_avg if past_oi_avg > 0 else 1.0
            
            logger.info(f"{csv_file} OI分析结果:")
            logger.info(f"  最近3次OI均值: {recent_oi_avg:.2f}")
            logger.info(f"  最近10次OI均值: {past_oi_avg:.2f}")
            logger.info(f"  OI增长比例: {oi_ratio:.2f}x")
            
            # 检查是否达到显著变化阈值
            if oi_ratio > 2.0:
                logger.info(f"  ✅ {csv_file} 的OI增长比例 {oi_ratio:.2f}x 超过阈值2.0")
            else:
                logger.info(f"  ❌ {csv_file} 的OI增长比例 {oi_ratio:.2f}x 未超过阈值2.0")
                
        except Exception as e:
            logger.error(f"分析 {csv_file} 时出错: {str(e)}")
    
    # 3. 收集实际数据并进行完整分析
    logger.info("\n开始收集实际数据并进行完整分析...")
    data = monitor.collect_data()
    
    if not data:
        logger.error("没有收集到数据，无法进行OI分析")
        return
    
    logger.info(f"成功收集了 {len(data)} 个交易对的数据")
    
    # 4. 分析OI变化
    oi_analysis_results, significant_oi_changes = monitor.analyze_oi_changes(data)
    
    logger.info(f"\nOI分析结果: 共分析了 {len(oi_analysis_results)} 个交易对")
    logger.info(f"发现 {len(significant_oi_changes)} 个显著的OI变化")
    
    # 5. 显示显著OI变化的详情
    if significant_oi_changes:
        logger.info("\n显著OI变化的交易对:")
        for i, item in enumerate(significant_oi_changes[:10]):  # 只显示前10个
            logger.info(f"{i+1}. {item['symbol']}: OI增长比例 = {item['oi_ratio']:.2f}x, 资金费率 = {item['funding_rate']:.4%}")
    else:
        logger.info("\n没有发现显著的OI变化")
        
        # 6. 检查OI比例接近阈值的交易对
        close_to_threshold = sorted([item for item in oi_analysis_results if item['oi_ratio'] > 1.7], 
                                   key=lambda x: x['oi_ratio'], reverse=True)
        
        if close_to_threshold:
            logger.info("\nOI增长比例接近阈值(>1.3)的交易对:")
            for i, item in enumerate(close_to_threshold[:10]):
                logger.info(f"{i+1}. {item['symbol']}: OI增长比例 = {item['oi_ratio']:.2f}x, 资金费率 = {item['funding_rate']:.4%}")
        else:
            logger.info("\n没有OI增长比例接近阈值的交易对")
    
    # 7. 建议
    logger.info("\n建议:")
    logger.info("1. 如果没有发现显著的OI变化，可以考虑降低阈值，当前阈值是2.0(100%增长)")
    logger.info("2. 确保数据收集正常，特别是OI数据")
    logger.info("3. 确保有足够的历史数据进行分析(至少10个数据点)")

if __name__ == "__main__":
    print("=" * 50)
    print("OI分析调试工具")
    print("=" * 50)
    
    debug_oi_analysis()
    
    print("\n" + "=" * 50)
    print("调试完成")
    print("=" * 50)
