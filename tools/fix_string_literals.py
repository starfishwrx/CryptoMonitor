#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复crypto_monitor.py中的未终止字符串字面量问题
"""

import os
import re

def fix_unterminated_strings(file_path):
    """修复未终止的字符串字面量"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复各种未终止的字符串字面量模式
    patterns = [
        # 修复消息构建部分的字符串
        (r'message \+= f"([^"]*)\n"', r'message += f"\1\\n"'),
        (r'message \+= "([^"]*)\n"', r'message += "\1\\n"'),
        
        # 修复emoji后面的换行
        (r'message \+= f"(🔴[^"]*)\(\{([^}]*)\}\)个\):\n"', r'message += f"\1(\{\2\})个):\\n"'),
        (r'message \+= f"(📈[^"]*)\(\{([^}]*)\}\)个\):\n"', r'message += f"\1(\{\2\})个):\\n"'),
        (r'message \+= f"(⚠️[^"]*)\(\{([^}]*)\}\)个\):\n"', r'message += f"\1(\{\2\})个):\\n"'),
        
        # 修复项目符号行
        (r'message \+= f"  • \{([^}]*)\}: \{([^}]*)\}\n"', r'message += f"  • \{\1\}: \{\2\}\\n"'),
        
        # 修复空行
        (r'message \+= "\n"', r'message += "\\n"'),
    ]
    
    # 应用所有修复模式
    fixed_content = content
    for pattern, replacement in patterns:
        fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # 保存修复后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"已修复 {file_path} 中的未终止字符串字面量")

def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建文件路径
    crypto_monitor_path = os.path.join(script_dir, "crypto_monitor.py")
    
    # 检查文件是否存在
    if not os.path.exists(crypto_monitor_path):
        print(f"文件不存在: {crypto_monitor_path}")
        return
    
    # 修复字符串字面量
    print("开始修复未终止的字符串字面量...")
    fix_unterminated_strings(crypto_monitor_path)
    print("修复完成！")

if __name__ == "__main__":
    main()
