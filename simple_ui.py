# -*- coding: utf-8 -*-
import gradio as gr
import json
import numpy as np
import os
from resume_chromadb_operater import add_resume, delete_resume, query_resume, similarity_search as resume_similarity_search, batch_add_resumes
from job_chromadb_operater import add_job, delete_job, query_job, similarity_search as job_similarity_search, batch_add_jobs
from send_message import send_batch_messages

def handle_resume_upload(file):
    """处理简历批量上传"""
    try:
        if file is None:
            return "请选择要上传的文件"
            
        if isinstance(file, list):
            file = file[0]
        
        with open(file.name, "r", encoding="utf-8") as f:
            resume_data = json.load(f)
            
        success_count = batch_add_resumes(resume_data)
        return f"成功导入 {success_count} 份简历"
    except Exception as e:
        return f"导入失败：{str(e)}"

def handle_job_upload(file):
    """处理岗位批量上传"""
    try:
        if file is None:
            return "请选择要上传的文件"
            
        if isinstance(file, list):
            file = file[0]
            
        with open(file.name, "r", encoding="utf-8") as f:
            job_data = json.load(f)
            
        success_count = batch_add_jobs(job_data)
        return f"成功导入 {success_count} 个岗位"
    except Exception as e:
        return f"导入失败：{str(e)}"

def process_matching(resume_text, company_text, display_option, sms_option):
    """处理匹配和发送"""
    try:
        # 查询简历
        resume_data = query_resume(resume_text)
        if not resume_data:
            return "未找到简历信息"
        
        # 获取岗位匹配
        results = job_similarity_search(resume_data['content'], n_results=10)
        if not results or not results['documents']:
            return "未找到匹配的岗位"
            
        # 提取匹配结果
        output = "匹配结果：\n" + "="*50 + "\n"
        
        # 如果需要显示详细信息
        if display_option:
            for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                output += f"\n岗位 {i}:\n"
                output += f"公司：{meta['company_name']}\n"
                output += f"专业要求：{meta['major']}\n"
                output += f"岗位链接：{meta['job_url']}\n"
                output += f"岗位详情：{doc[:200]}...\n"
                output += "-"*30 + "\n"
        
        # 如果需要发送短信
        if sms_option:
            # 构建短信数据
            today = datetime.today()
            date_str = f"{today.year}年{today.month}月{today.day}日"
            
            job_urls = [meta.get('job_url', '') for meta in results['metadatas'][0]]
            sms_content = f"亲爱的毕业生同学{resume_data['metadata']['name']}：\n" \
                         f"您好！为帮助大家提高应聘成功率，精准瞄准应聘岗位，学校根据同学们在就业信息网填写的简历，" \
                         f"与企业岗位需求进行精准匹配，已为您筛选出{len(job_urls)}个适配度高的岗位。点击下方链接，即可查看岗位详情：\n"
            
            for i, url in enumerate(job_urls, 1):
                sms_content += f"岗位{i}：{url}\n"
                
            sms_content += f"\n这些推荐岗位会随您简历完善、内容更新及新岗位发布而变化。" \
                          f"建议您定期查收短信或关注学校就业信息网、”深技大就业”公众号、学院通知等相关通知，以免错过合适机会。\n\n" \
                          f"深圳技术大学学生就业指导中心\n{date_str}"
            
            # 发送短信
            message_data = [{
                "name": resume_data['metadata']['name'],
                "mobile": resume_data['metadata'].get('mobile', ''),
                "content": sms_content
            }]
            
            result = send_batch_messages(message_data)
            output += f"\n短信发送结果：成功 {result['success']} 条，失败 {result['fail']} 条"
            
        return output
    except Exception as e:
        return f"处理失败：{str(e)}"

def search_similar_jobs_by_resume(name, stu_id, resume_content, num_results=10):
    """根据简历内容搜索匹配的岗位
    Args:
        name: str, 学生姓名
        stu_id: str, 学号
        resume_content: str, 简历内容
        num_results: int, 返回结果数量，默认10条
    Returns:
        str: 格式化的匹配结果
    """
    results = job_similarity_search(resume_content, n_results=num_results)
    if results and results['documents']:
        output = f"为 {name}（学号：{stu_id}）匹配到的推荐岗位：\n"
        output += "-" * 50 + "\n"
        
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0],
            results['distances'][0]
        )):
            match_score = map_distance_to_score(distance)  # 将距离转换为相似度分数
            
            output += f"\n=== 推荐岗位 {i+1} (匹配度: {match_score:.1f}%) ===\n"
            output += f"公司名称：{meta['company_name']}\n"
            output += f"岗位ID：{meta['job_id']}\n"
            output += f"专业要求：{meta['major']}\n"
            output += f"岗位链接：{meta['job_url']}\n"
            output += f"岗位详情：\n{doc}\n"
            output += "-" * 30 + "\n"
        return output
    return f"未找到与 {name} 简历匹配的岗位。"

def send_job_recommendations_sms(file):
    """处理发送岗位推荐短信"""
    try:
        if file is None:
            return "请选择要上传的文件"
            
        if isinstance(file, list):
            file = file[0]
            
        print("\n" + "="*50)
        print("[DEBUG] 开始处理短信发送")
        print(f"[DEBUG] 文件类型: {type(file)}")
        
        if hasattr(file, "name"):
            print(f"[DEBUG] 读取文件: {file.name}")
            with open(file.name, "r", encoding="utf-8") as f:
                students_data = json.load(f)
                print(f"[DEBUG] 读取到的学生数据: {len(students_data)}条")
                print(f"[DEBUG] 第一条数据示例: {students_data[0] if students_data else 'No data'}")
        else:
            content = file.decode('utf-8')
            students_data = json.loads(content)
        
        from datetime import datetime
        today = datetime.today()
        date_str = f"{today.year}年{today.month}月{today.day}日"
        
        messages_data = []
        for idx, student in enumerate(students_data):
            name = student.get('name')
            mobile = student.get('mobile')
            resume_content = student.get('resume_content', '')
            
            print(f"\n[DEBUG] 处理第{idx+1}个学生:")
            print(f"[DEBUG] 姓名: {name}")
            print(f"[DEBUG] 手机: {mobile}")
            print(f"[DEBUG] 简历内容长度: {len(resume_content)}")
            
            if not all([name, mobile, resume_content]):
                print(f"[DEBUG] 数据不完整: {student}")
                continue
            
            results = job_similarity_search(resume_content, n_results=2)
            if not results or not results['documents']:
                print(f"[DEBUG] 未找到匹配岗位")
                continue
                
            job_urls = [meta.get('job_url', '') for meta in results['metadatas'][0][:10]]
            job_urls = [url for url in job_urls if url]
            
            print(f"[DEBUG] 匹配到的岗位数量: {len(job_urls)}")
            
            if not job_urls:
                print(f"[DEBUG] 无有效岗位链接")
                continue
            
            content = f"亲爱的毕业生同学{name}：\n" \
                     f"您好！为帮助大家提高应聘成功率，精准瞄准应聘岗位，学校根据同学们在就业信息网填写的简历，" \
                     f"与企业岗位需求进行精准匹配，已为您筛选出{len(job_urls)}个适配度高的岗位。点击下方链接，即可查看岗位详情：\n"
            
            for i, url in enumerate(job_urls, 1):
                content += f"岗位{i}：{url}\n"
            
            content += f"\n这些推荐岗位会随您简历完善、内容更新及新岗位发布而变化。" \
                     f"建议您定期查收短信或关注学校就业信息网、“深技大就业”公众号、学院通知等相关通知，以免错过合适机会。\n\n" \
                     f"深圳技术大学学生就业指导中心\n" \
                     f"{date_str}"
            
            print(f"[DEBUG] 短信内容长度: {len(content)}")
            print(f"[DEBUG] 短信内容前200字符: {content[:200]}...")
            
            messages_data.append({
                "name": name,
                "mobile": mobile,
                "content": content
            })
        
        if not messages_data:
            return "没有需要发送的短信数据"
            
        print(f"\n[DEBUG] 准备发送 {len(messages_data)} 条短信")
        print("[DEBUG] 第一条短信数据示例:")
        print(f"手机号: {messages_data[0]['mobile']}")
        print(f"姓名: {messages_data[0]['name']}")
        print(f"内容长度: {len(messages_data[0]['content'])}")
        
        result = send_batch_messages(messages_data)
        print(f"\n[DEBUG] 发送结果: {result}")
        
        if not result:
            return "发送失败：未收到发送结果"
            
        return f"发送完成！成功：{result['success']}条，失败：{result['fail']}条\n" \
               f"总计尝试发送：{len(messages_data)}条"
               
    except Exception as e:
        print(f"[DEBUG] 发送异常: {str(e)}")
        import traceback
        print("[DEBUG] 异常堆栈:")
        print(traceback.format_exc())
        return f"发送失败：{str(e)}"

def map_distance_to_score(distance):
    """将余弦距离映射到45-95的分数区间，使用sigmoid函数实现非线性映射
    - 分数主要集中在55-85区间
    - 45-55和85-95各占约15%的比例
    """
    # 首先将distance转换为初始分数
    raw_score = (1 - distance) * 100
    
    # 使用sigmoid函数进行非线性映射
    def sigmoid(x, k=0.15):
        return 1 / (1 + np.exp(-k * (x - 50)))
    
    # 映射到45-95区间
    mapped_score = 45 + 50 * sigmoid(raw_score)
    return mapped_score

# 创建 Gradio 界面
with gr.Blocks(css="body {background-image: url('static/background.png'); background-size: cover;}") as demo:
    gr.Markdown("<h1 style='text-align: center; color: #005bbb;'>深圳技术大学就业招聘数字人系统</h1>", 
                )
    gr.Markdown("<h2 style='text-align: center;'>—— 润小职 ——</h2>", 
                )
    
   

    with gr.Row():
        with gr.Column():
            resume_file = gr.File(label="简历JSON文件")
            resume_upload_btn = gr.Button("批量导入简历")
            resume_output = gr.Textbox(label="简历导入结果")
            resume_upload_btn.click(
                handle_resume_upload,
                inputs=[resume_file],
                outputs=[resume_output]
            )

    with gr.Column():
            job_file = gr.File(label="岗位JSON文件")
            job_upload_btn = gr.Button("批量导入岗位")
            job_output = gr.Textbox(label="岗位导入结果")
            job_upload_btn.click(
                handle_job_upload,
                inputs=[job_file],
                outputs=[job_output]
            )
    
    with gr.Row():
        with gr.Column():
            sms_file = gr.File(label="推荐短信JSON文件")
            sms_send_btn = gr.Button("发送岗位推荐短信", variant="primary")
            sms_output = gr.Textbox(label="发送结果")
            sms_send_btn.click(
                send_job_recommendations_sms,
                inputs=[sms_file],
                outputs=[sms_output]
            )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)