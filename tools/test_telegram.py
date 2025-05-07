#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Bot测试工具
用于测试Telegram Bot配置是否正确，能否成功发送消息
"""

import os
import sys
import requests
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("telegram_test.log")
    ]
)
logger = logging.getLogger(__name__)

def test_telegram_bot():
    """测试Telegram Bot配置"""
    # 加载环境变量
    load_dotenv()
    
    # 获取Telegram配置
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # 检查配置是否存在
    if not bot_token:
        logger.error("未找到TELEGRAM_BOT_TOKEN环境变量")
        print("错误: 未找到TELEGRAM_BOT_TOKEN环境变量。请在.env文件中设置。")
        return False
    
    if not chat_id:
        logger.error("未找到TELEGRAM_CHAT_ID环境变量")
        print("错误: 未找到TELEGRAM_CHAT_ID环境变量。请在.env文件中设置。")
        return False
    
    # 打印配置信息（隐藏部分Token）
    print(f"Bot Token: {bot_token[:5]}...{bot_token[-5:]}")
    print(f"Chat ID: {chat_id}")
    
    # 验证Bot Token
    try:
        logger.info("正在验证Bot Token...")
        verify_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        verify_response = requests.get(verify_url)
        verify_data = verify_response.json()
        
        if verify_response.status_code != 200 or not verify_data.get('ok'):
            logger.error(f"Bot Token验证失败: {verify_response.text}")
            print(f"错误: Bot Token无效。API响应: {verify_response.text}")
            return False
        
        bot_username = verify_data.get('result', {}).get('username')
        logger.info(f"Bot Token验证成功，机器人用户名: @{bot_username}")
        print(f"Bot Token验证成功，机器人用户名: @{bot_username}")
    except Exception as e:
        logger.error(f"验证Bot Token时出错: {str(e)}")
        print(f"错误: 验证Bot Token时出错: {str(e)}")
        return False
    
    # 发送测试消息
    try:
        logger.info(f"正在发送测试消息到Chat ID: {chat_id}...")
        message = f"这是一条测试消息，发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        
        response = requests.post(url, data=payload)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('ok'):
            logger.info("测试消息发送成功")
            print("✅ 测试消息发送成功！")
            print("如果您没有收到消息，请检查以下几点:")
            print("1. 您是否已经向机器人发送过消息（这是Telegram的安全要求）")
            print("2. Chat ID是否正确")
            print("3. 网络连接是否正常")
            return True
        else:
            logger.error(f"发送测试消息失败: {response.text}")
            print(f"错误: 发送测试消息失败。API响应: {response.text}")
            
            # 检查是否有错误描述
            if 'description' in response_data:
                error_desc = response_data['description']
                logger.error(f"错误描述: {error_desc}")
                print(f"错误描述: {error_desc}")
                
                # 提供常见错误的解决方案
                if "chat not found" in error_desc.lower():
                    print("\n可能的解决方案:")
                    print("- 确保Chat ID正确")
                    print("- 确保您已经向机器人发送过至少一条消息")
                elif "unauthorized" in error_desc.lower():
                    print("\n可能的解决方案:")
                    print("- 检查Bot Token是否正确")
                    print("- 尝试重新创建机器人")
                elif "blocked" in error_desc.lower():
                    print("\n可能的解决方案:")
                    print("- 您可能已阻止该机器人，请在Telegram中取消阻止")
            
            return False
    except Exception as e:
        logger.error(f"发送测试消息时出错: {str(e)}")
        print(f"错误: 发送测试消息时出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("Telegram Bot 测试工具")
    print("=" * 50)
    print("此工具将测试您的Telegram Bot配置是否正确\n")
    
    success = test_telegram_bot()
    
    print("\n" + "=" * 50)
    if success:
        print("测试完成: 配置正确")
    else:
        print("测试完成: 配置有误")
        print("请查看上方错误信息并修复问题")
        print("参考telegram_bot_setup.md文件获取更多帮助")
    print("=" * 50)

if __name__ == "__main__":
    main()
