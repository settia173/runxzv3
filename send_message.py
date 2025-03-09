# -*- coding: utf-8 -*-
import requests
import hashlib
from typing import List, Dict
import json

def send_message(mobile, content, user_id="xsjyzdzx", password="92053811", url="http://10.1.12.218:8088/websms/smsJsonService"):
    """
    发送短信的函数
    
    Args:
        mobile (str): 接收短信的手机号
        content (str): 短信内容（不需要包含签名，会自动添加）
        user_id (str, optional): 企业账号. Defaults to "xsjyzdzx".
        password (str, optional): 企业密码. Defaults to "92053811".
        url (str, optional): 短信接口URL. Defaults to "http://10.1.12.218:8088/websms/smsJsonService".
    
    Returns:
        dict: 接口返回的结果
    """
    # 计算密码MD5值
    md5_password = hashlib.md5(password.encode('utf-8')).hexdigest()
    
    # 拼接完整短信内容（添加签名）
    if not content.startswith("【深圳技术大学】"):
        content = f"【深圳技术大学】{content}"
    
    # 构造请求数据
    post_data = {
        "action": "sendsms",
        "userId": user_id,
        "md5password": md5_password,
        "content": content,
        "mobile": mobile,
    }
    
    try:
        # 发送请求
        response = requests.post(url, data=post_data)
        return response.json()  # 假设返回的是JSON格式
    except Exception as e:
        return {"error": str(e)}

def send_batch_messages(data_list: List[Dict]) -> Dict:
    """
    批量发送短信
    
    Args:
        data_list: 包含多个字典的列表，每个字典必须包含 name、mobile 和 content 字段
        例如：[{
            "name": "张三", 
            "mobile": "13800138000",
            "content": "这是短信内容"
        }, ...]
            
    Returns:
        dict: 发送结果统计，包含成功和失败的数量及详细信息
    """
    success_count = 0
    fail_count = 0
    failed_records = []
    
    for data in data_list:
        name = data.get('name')
        mobile = data.get('mobile')
        content = data.get('content')
        
        if not all([name, mobile, content]):
            fail_count += 1
            failed_records.append({
                "name": name,
                "mobile": mobile,
                "error": "缺少必要信息"
            })
            continue
            
        try:
            # 调用单条发送函数
            result = send_message(
                mobile=mobile,
                content=content
            )
            
            if result.get('error'):
                fail_count += 1
                failed_records.append({
                    "name": name,
                    "mobile": mobile,
                    "error": result['error']
                })
            else:
                success_count += 1
                
        except Exception as e:
            fail_count += 1
            failed_records.append({
                "name": name,
                "mobile": mobile,
                "error": str(e)
            })
    
    return {
        "total": len(data_list),
        "success": success_count,
        "fail": fail_count,
        "failed_records": failed_records
    }


def test_send_message():
    # 测试发送短信
    test_cases = [
        {
        "name": "张三",
        "stu_ids": "66",
        "mobile": "15873049129",
        "content": "测试数据测试113113深圳技术大学"
        },
        {
      "name": "李四",
      "stu_ids": "67",
      "mobile": "13148802576",
      "content": "测试数据测试1314880深圳技术大学"
      }
        # 可以添加更多测试用例
    ]
    
    for case in test_cases:
        print(f"发送短信到: {case['mobile']}")
        print(f"短信内容: {case['content']}")
        result = send_message(case['mobile'], case['content'])
        print(f"发送结果: {result}")
        print("-" * 50)

if __name__ == "__main__":
    test_send_message()
    