import hashlib
import json
import re
from datetime import datetime
import requests
import gradio as gr
def get_student_mobile(student_id):
    """
    根据学号获取学生手机号
    从学生简历中提取手机号
    
    参数:
    student_id: 学生学号
    
    返回:
    str: 学生手机号
    """
    try:
        # 1. 优先从向量数据库查询
        from resume_chromadb_operater import query_resume
        resume_data = query_resume(student_id)
        if resume_data and resume_data.get("metadata", {}).get("mobile"):
            return resume_data["metadata"]["mobile"]

        # 2. 尝试从匹配结果文件中查询
        for file in os.listdir():
            if file.startswith("match_result_") and file.endswith(".json"):
                with open(file, 'r', encoding='utf-8') as f:
                    match_results = json.load(f)
                    for student in match_results:
                        if student.get('stu_id') == student_id:
                            # 如果匹配结果中有手机号字段
                            if 'mobile' in student and student['mobile']:
                                return student['mobile']
        
        # 2. 尝试从临时文件中查询
        temp_file = f"temp_resume_{student_id}.json"
        if os.path.exists(temp_file):
            with open(temp_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
                if 'mobile' in resume_data and resume_data['mobile']:
                    return resume_data['mobile']
        
        # 3. 尝试从向量数据库中查询
        try:
            from resume_chromadb_operater import query_resume
            resume_data = query_resume(student_id)
            if resume_data and 'mobile' in resume_data and resume_data['mobile']:
                return resume_data['mobile']
        except Exception as e:
            print(f"从向量数据库查询手机号失败: {str(e)}")
        
        # 4. 从简历内容中提取手机号
        # 尝试从临时文件中的简历内容提取
        if os.path.exists(temp_file):
            with open(temp_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
                content = resume_data.get('resume_content', '')
                # 使用正则表达式匹配手机号
                mobile_match = re.search(r'1[3-9]\d{9}', content)
                if mobile_match:
                    return mobile_match.group(0)
        
        # 5. 如果以上方法都失败，返回默认手机号
        print(f"未能找到学号 {student_id} 的手机号，使用默认号码")
        return "13723728369"  # 默认手机号
    except Exception as e:
        print(f"获取手机号时出错: {str(e)}")
        return "13723728369"  # 出错时返回默认手机号


# 短信发送函数
def send_sms(mobile, content, sign="深圳技术大学"):
    """发送短信的函数
    
    Args:
        mobile: 接收短信的手机号
        content: 短信内容 (不含签名)
        sign: 短信签名
    
    Returns:
        dict: 包含发送状态和消息的字典
    """
    try:
        # 验证手机号格式
        if not mobile or not re.match(r'^1[3-9]\d{9}$', str(mobile)):
            return {"success": False, "message": f"无效的手机号: {mobile}"}
        # 目标接口URL和参数
        password = "92053811"
        post_url = "http://10.1.12.218:8088/websms/smsJsonService"
        md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
        
        # 构建完整短信内容
        full_content = f"【{sign}】{content}"
        
        post_data = {
            "action": "sendsms",
            "userId": "xsjyzdzx",  # 企业帐号
            "md5password": md5,  # 企业密码
            "content": full_content,
            "mobile": str(mobile),
        }
        print(f"发送短信请求: {post_data}")
        response = requests.post(post_url, data=post_data)
        result = response.text
        print(f"短信发送响应: {result}")
        
        # 检查响应是否包含成功信息
        if "success" in result.lower() or "成功" in result:
            return {"success": True, "message": "短信发送成功", "response": result}
        else:
            return {"success": False, "message": f"短信发送失败: {result}", "response": result}
    except Exception as e:
        print(f"短信发送失败: {str(e)}")
        return {"success": False, "message": f"短信发送失败: {str(e)}"}

# 个人匹配后发送通知
def send_match_notification(student_id=None, current_id=None, result_data=None):
    """发送个人匹配结果通知
    
    Args:
        result_data: 匹配结果数据
        student_id: 学生学号(用于在数据库中查找)
    
    Returns:
        str: 操作结果信息
    """
    # 如果没有直接提供结果数据，尝试通过学号查找
    actual_id = student_id if student_id else current_id
    try:
        # 检查是否提供了学号
        if not actual_id:
            return "请先填写学号或上传简历"
            
        print(f"尝试为学号 {student_id} 发送通知")
        
        # 获取学生手机号
        mobile = get_student_mobile(actual_id)
        
        if not mobile or mobile == "13723728369":  # 检查是否为默认手机号
            return "未找到有效的手机号码，请确保已填写手机号"
            
        print(f"获取到手机号: {mobile}")
        
        # 构建短信内容
        sms_content = f"您好，您的求职简历已匹配到合适岗位，请登录就业系统查看详情。"
        
        # 发送短信
        result = send_sms(mobile, sms_content)
        
        if result["success"]:
            return f"<div style='color:green'>匹配结果通知已发送至 {mobile}</div>"
        else:
            return f"<div style='color:red'>发送失败: {result['message']}</div>"
    except Exception as e:
        print(f"发送通知时出错: {str(e)}")
        return f"<div style='color:red'>发送通知时出错: {str(e)}</div>"

# 批量发送匹配结果通知
def batch_send_notifications(result_file):
    """批量发送匹配结果通知
    
    Args:
        result_file: 匹配结果文件路径
    
    Returns:
        str: 包含发送统计信息的HTML
    """
    progress = gr.Progress()
    
    # 加载匹配结果文件
    try:
        progress(0.1, desc="读取匹配结果...")
        with open(result_file.name, 'r', encoding='utf-8') as f:
            match_results = json.load(f)
    except Exception as e:
        return f"<div style='color:red'>读取匹配结果文件失败: {str(e)}</div>"
    
    total = len(match_results)
    success_count = 0
    failed_count = 0
    failed_students = []
    
    progress(0.2, desc="准备发送通知...")
    
    # 遍历每个学生的匹配结果发送通知
    for i, student in enumerate(match_results):
        progress(0.2 + 0.7 * (i/total), desc=f"正在发送 ({i+1}/{total})...")
        student_name = student.get('name', '未知学生')
        student_id = student.get('stu_id', '')
        mobile = student.get('mobile', '')
        if not mobile:
            mobile = get_student_mobile(student_id)
        
        if not mobile:
            failed_count += 1
            failed_students.append({"name": student_name, "id": student_id, "error": "未找到手机号"})
            continue
        
        # 获取学生的匹配结果
        if student.get('matched_jobs'):
            top_jobs = student['matched_jobs'][:3]  # 取前3个匹配岗位
            current_date = datetime.now().strftime("%Y{}%m{}%d{}".format("年", "月", "日"))
            
            # 构建岗位链接列表
            job_links = []
            for idx, job in enumerate(top_jobs, 1):
                job_url = job.get('job_url', '').replace('\\', '/')
                job_links.append(f"岗位{idx}：{job_url}" if job_url else f"岗位{idx}：暂无链接")
            
            # 构建短信内容
            sms_content = f"""亲爱的毕业生同学：
 您好！为帮助大家提高应聘成功率，精准瞄准应聘岗位，学校根据同学们在就业信息网填写的简历，与企业岗位需求进行精准匹配，已为您筛选出{len(top_jobs)}个适配度高的岗位。点击下方链接，即可查看岗位详情：
{chr(10).join(job_links)}

这些推荐岗位会随您简历完善、内容更新及新岗位发布而变化。建议您定期查收短信或关注学校就业信息网、“深技大就业”公众号、学院通知等相关通知，以免错过合适机会。

深圳技术大学学生就业指导中心
{current_date}"""

            # 发送短信
            result = send_sms(mobile, sms_content)
            
            if result["success"]:
                success_count += 1
            else:
                failed_count += 1
                failed_students.append({"name": student_name, "id": student_id, "error": result["message"]})
        else:
            failed_count += 1
            failed_students.append({"name": student_name, "id": student_id, "error": "无匹配结果"})
    
    progress(1.0, desc="发送完成！")
    
    # 生成发送报告
    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 20px auto;">
        <h3 style="color: #003788;">短信通知发送报告</h3>
        <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <p><strong>总计:</strong> {total}条</p>
            <p><strong>成功:</strong> <span style="color:green">{success_count}条</span></p>
            <p><strong>失败:</strong> <span style="color:red">{failed_count}条</span></p>
        </div>
    """
    
    if failed_students:
        html += """
        <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="color: #e74c3c;">发送失败列表</h4>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f2f6fc;">
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">姓名</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">学号</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">错误信息</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for student in failed_students:
            html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{student['name']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{student['id']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{student['error']}</td>
                </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    # 添加弹窗脚本
    html += f"""
    </div>
    <script>
        // 使用模板字符串传递统计信息
        const msg = `批量发送完成！\\n成功：{success_count}条 | 失败：{failed_count}条`;
        
        // 成功时显示绿色弹窗
        {"alert(`${msg}`);" if success_count > 0 else ""}
        
        // 失败时显示红色提示
        {"alert(`${msg}`);" if failed_count > 0 else ""}
    </script>
    """

    html += "</div>"
    return html

# 批量结果展示HTML生成
def build_batch_results_html(results):
    html = """<div style="font-family: 'Segoe UI', sans-serif; max-width: 90%; margin: 20px auto;">
    <h2 style="text-align: center; color: #003788;">批量匹配结果摘要</h2>
    <p style="text-align: center; color: #666;">已为 {student_count} 名学生匹配岗位，每人提供 {job_count} 个岗位推荐</p>
    """.format(student_count=len(results), job_count=len(results[0]["matched_jobs"]) if results else 0)
    
    for student in results:
        html += f"""
        <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 30px; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h3 style="margin-bottom: 10px; color: #003788;">{student['name']} <span style="color: #666; font-size: 0.8em;">({student['stu_id']})</span></h3>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background-color: #f2f6fc;">
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">排名</th>
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">公司</th>
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">匹配度</th>
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">链接</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for i, job in enumerate(student['matched_jobs']):
            match_score = int(job['score'])
            html += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #eee;">#{i+1}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee;">{job['company_name']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee;">
                        <div style="background: {get_score_color(match_score)}; 
                                  display: inline-block; padding: 5px 10px; border-radius: 12px; 
                                  color: white; font-weight: bold;">
                            {match_score}%
                        </div>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee;">
                        <a href="{job['job_url']}" target="_blank" 
                           style="text-decoration: none; color: #0068ca;">查看详情</a>
                    </td>
                </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    html += """</div>"""
    return html