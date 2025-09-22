#!/usr/bin/env python3
"""
測試 Debug 訊息清理結果
檢查是否還有殘留的 debug print 語句
"""

import os
import re
from pathlib import Path

def check_debug_messages():
    """檢查是否還有 debug 訊息"""
    print("🔍 檢查 Debug 訊息清理結果...")
    
    # 定義要檢查的檔案模式
    yolo_backend_dir = Path("yolo_backend")
    patterns_to_check = [
        r'print\(f["\'].*\[DEBUG\]',
        r'print\(f["\'].*🔍.*DEBUG',
        r'print\(f["\'].*📝.*DEBUG',
        r'print\(f["\'].*✅.*DEBUG',
        r'print\(f["\'].*⚠️.*DEBUG',
        r'print\(f["\'].*❌.*DEBUG',
        r'print\(f["\'].*🤖.*\[YOLO\]',
        r'print\(f["\'].*📊.*\[YOLO\]',
        r'print\(f["\'].*🖼️.*\[YOLO\]',
        r'print\(f["\'].*⏱️.*\[YOLO\]'
    ]
    
    debug_found = False
    info_messages = []
    
    # 檢查所有 .py 檔案
    for py_file in yolo_backend_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in patterns_to_check:
                        if re.search(pattern, line):
                            print(f"❌ 發現殘留 debug 訊息: {py_file}:{line_num}")
                            print(f"   內容: {line.strip()}")
                            debug_found = True
                    
                    # 檢查是否有其他可疑的 print 語句
                    if 'print(f"' in line and any(emoji in line for emoji in ['🔍', '📝', '✅', '⚠️', '❌']):
                        if 'DEBUG' not in line and line.strip() not in info_messages:
                            info_messages.append(f"{py_file}:{line_num} - {line.strip()}")
                            
        except Exception as e:
            print(f"⚠️ 無法讀取檔案 {py_file}: {e}")
    
    if not debug_found:
        print("✅ 所有 DEBUG 訊息已成功清理！")
    
    if info_messages:
        print(f"\n📋 發現 {len(info_messages)} 條資訊性訊息（保留）:")
        for msg in info_messages[:10]:  # 只顯示前10條
            print(f"   {msg}")
        if len(info_messages) > 10:
            print(f"   ... 還有 {len(info_messages) - 10} 條")
    
    return not debug_found

if __name__ == "__main__":
    success = check_debug_messages()
    if success:
        print("\n🎉 Debug 訊息清理完成！系統已準備好用於生產環境。")
    else:
        print("\n⚠️ 仍有 Debug 訊息需要清理。")
