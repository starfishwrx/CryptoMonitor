#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接测试Telegram Bot
使用硬编码的Token和Chat ID进行测试，避免环境变量加载问题
"""

import requests
import sys
from datetime import datetime

def test_telegram():
    # 直接使用配置的值
    bot_token = "7815032438:AAFZ8n_gfUVKfVU3TWQGDvw0qTkkmBJtJuU"
    chat_id = "6147961314"
    
    print(f"使用Bot Token: {bot_token[:5]}...{bot_token[-5:]}")
    print(f"使用Chat ID: {chat_id}")
    
    # 1. 验证Bot Token
    print("\n1. 验证Bot Token...")
    try:
        verify_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        verify_response = requests.get(verify_url)
        verify_data = verify_response.json()
        
        print(f"API响应: {verify_response.text}")
        
        if verify_response.status_code != 200 or not verify_data.get('ok'):
            print(f"错误: Bot Token无效")
            return False
        
        bot_username = verify_data.get('result', {}).get('username')
        print(f"Bot Token验证成功，机器人用户名: @{bot_username}")
    except Exception as e:
        print(f"错误: 验证Bot Token时出错: {str(e)}")
        return False
    
    # 2. 发送测试消息
    print("\n2. 发送测试消息...")
    try:
        message = f"这是一条测试消息，发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        
        print(f"发送消息: {message}")
        print(f"请求URL: {url}")
        print(f"请求参数: {payload}")
        
        response = requests.post(url, data=payload)
        response_data = response.json()
        
        print(f"API响应: {response.text}")
        
        if response.status_code == 200 and response_data.get('ok'):
            print("\n消息发送成功！")
            print("如果您没有收到消息，请检查以下几点:")
            print("1. 您是否已经向机器人发送过消息（这是Telegram的安全要求）")
            print("2. 网络连接是否正常")
            return True
        else:
            print(f"\n错误: 发送消息失败")
            
            # 检查是否有错误描述
            if 'description' in response_data:
                error_desc = response_data['description']
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
        print(f"错误: 发送消息时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Telegram Bot 直接测试")
    print("=" * 50)
    
    success = test_telegram()
    
    print("\n" + "=" * 50)
    if success:
        print("测试完成: 配置正确")
    else:
        print("测试完成: 配置有误")
    print("=" * 50)
