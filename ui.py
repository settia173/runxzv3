# -*- coding: utf-8 -*-
import gradio as gr
import json
import numpy as np
import os
from resume_chromadb_operater import add_resume, delete_resume, query_resume, similarity_search as resume_similarity_search, batch_add_resumes
from job_chromadb_operater import add_job, delete_job, query_job, similarity_search as job_similarity_search, batch_add_jobs
from send_message import send_batch_messages

def add_resume_ui(name, stu_id,resume_content):
    """添加简历的UI处理函数"""
    resume_data = {
        "name": name,
        "stu_ids": stu_id,
        "resume_content": resume_content
    }
    success = add_resume(resume_data)
    if success:
        return "简历添加成功！"
    return "简历添加失败，请检查输入数据。"

def delete_resume_ui(stu_id):
    """删除简历的UI处理函数"""
    success = delete_resume(stu_id)
    if success:
        return "简历删除成功！"
    return "简历删除失败，请检查学号是否存在。"

def query_resume_ui(stu_id):
    """查询简历的UI处理函数"""
    result = query_resume(stu_id)
    if result:
        return f"学生姓名：{result['metadata']['name']}\n学生学号：{result['metadata']['stu_id']}\n学生电话：{result['metadata']['mobiles']}\n简历内容：\n{result['content']}"
    return "未找到对应学号的简历信息。"

def search_similar_resumes_by_job(company_name, job_id, job_requirements, job_responsibilities, major="", job_url="", num_results=10):
    """根据岗位信息搜索匹配的简历
    Args:
        company_name: str, 公司名称
        job_id: str, 岗位ID
        job_requirements: str, 岗位要求
        job_responsibilities: str, 岗位职责
        major: str, 专业要求，默认为空
        job_url: str, 岗位链接，默认为空
        num_results: int, 返回结果数量，默认10条
    Returns:
        str: 格式化的匹配结果
    """
    # 组合查询文本
    query_text = f"{job_requirements} {job_responsibilities} {major}".strip()
    
    # 调用简历库的相似度搜索
    results = resume_similarity_search(query_text, n_results=num_results)
    
    if results and results['documents']:
        output = f"为 {company_name}（岗位ID：{job_id}）匹配到的推荐简历：\n"
        output += "-" * 50 + "\n"
        
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0],
            results['distances'][0]
        )):
            match_score = map_distance_to_score(distance)  # 将距离转换为相似度分数
            
            output += f"\n=== 推荐简历 {i+1} (匹配度: {match_score:.1f}%) ===\n"
            output += f"学生姓名：{meta['name']}\n"
            output += f"学号：{meta['stu_id']}\n"
            output += f"简历内容：\n{doc}\n"
            output += "-" * 30 + "\n"
        return output
    return f"未找到与该岗位匹配的简历。"

def add_job_ui(company_name, job_id, major, job_url, requirements, responsibilities):
    """添加岗位的UI处理函数"""
    job_data = {
        "company_name": company_name,
        "job_id": job_id,
        "major": major,
        "job_url": job_url,
        "job_requirements": requirements,
        "job_responsibilities": responsibilities
    }
    success = add_job(job_data)
    if success:
        return "岗位添加成功！"
    return "岗位添加失败，请检查输入数据。"

def delete_job_ui(job_id):
    """删除岗位的UI处理函数"""
    success = delete_job(job_id)
    if success:
        return "岗位删除成功！"
    return "岗位删除失败，请检查岗位ID是否存在。"

def query_job_ui(job_id):
    """查询岗位的UI处理函数"""
    result = query_job(job_id)
    if result:
        return f"公司名称：{result['metadata']['company_name']}\n" \
               f"专业要求：{result['metadata']['major']}\n" \
               f"岗位链接：{result['metadata']['job_url']}\n\n" \
               f"岗位详情：\n{result['content']}"
    return "未找到对应岗位ID的信息。"

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

def handle_resume_json_upload(file):
    """处理简历JSON文件上传"""
    try:
        if file is None:
            return "请选择要上传的文件"
            
        if isinstance(file, list):
            file = file[0]  # Gradio可能返回文件列表

        print(f"文件类型: {type(file)}")   

        if hasattr(file, "name"):  # 新版本Gradio
            with open(file.name, "r", encoding="utf-8") as f:
                resume_data = json.load(f)
                print(f"读取到的数据: {resume_data[:2]}")  # 打印前两条数据
        else:  # 兼容处理
            content = file.decode('utf-8')
            resume_data = json.loads(content)
            print(f"解码后的数据: {resume_data[:2]}")  # 打印前两条数据
            
        if not isinstance(resume_data, list):
            return "上传的JSON文件格式错误，应为简历列表"
            
        # 检查数据格式
        for idx, resume in enumerate(resume_data):
            if not all(key in resume for key in ["name", "stu_ids", "resume_content"]):
                return f"第{idx+1}条数据缺少必要字段(name/stu_ids/resume_content)"
            
        success_count = batch_add_resumes(resume_data)
        
        # 验证添加结果
        print(f"尝试添加的总数: {len(resume_data)}")
        print(f"成功添加数量: {success_count}")
        
        if success_count == 0:
            return "导入失败：未能成功添加任何简历"
        
        return f"成功导入 {success_count} 份简历"
    except Exception as e:
        print(f"导入异常: {str(e)}")  # 打印详细错误信息
        return f"导入失败：{str(e)}"

def handle_job_json_upload(file):
    """处理岗位JSON文件上传"""
    try:
        if file is None:
            return "请选择要上传的文件"
            
        if isinstance(file, list):
            file = file[0]  # Gradio可能返回文件列表
            
        if hasattr(file, "name"):  # 新版本Gradio
            with open(file.name, "r", encoding="utf-8") as f:
                job_data = json.load(f)
        else:  # 兼容处理
            content = file.decode('utf-8')
            job_data = json.loads(content)
            
        success_count = batch_add_jobs(job_data)
        return f"成功导入 {success_count} 个岗位"
    except Exception as e:
        return f"导入失败：{str(e)}"

def send_job_recommendations_sms(file):
    """处理发送岗位推荐短信"""
    try:
        if file is None:
            return "请选择要上传的文件"
            
        if isinstance(file, list):
            file = file[0]
            
        print("=" * 50)
        print(f"文件类型: {type(file)}")
        
        if hasattr(file, "name"):
            print(f"读取文件: {file.name}")
            with open(file.name, "r", encoding="utf-8") as f:
                students_data = json.load(f)
                print(f"读取到的学生数据: {len(students_data)}条")
        else:
            content = file.decode('utf-8')
            students_data = json.loads(content)
        
        # 获取当前日期
        from datetime import datetime
        today = datetime.today()
        date_str = f"{today.year}年{today.month}月{today.day}日"
        
        messages_data = []
        for idx, student in enumerate(students_data):
            name = student.get('name')
            mobile = student.get('mobile')
            stu_id = student.get('stu_id', '')
            resume_content = student.get('resume_content', '')
            
            print(f"处理第{idx+1}个学生: {name}, 手机: {mobile}")
            
            if not all([name, mobile, resume_content]):
                print(f"数据不完整: {student}")
                continue
            
            # 获取岗位推荐
            results = job_similarity_search(resume_content, n_results=10)
            if not results or not results['documents']:
                print(f"未找到匹配岗位: {name}")
                continue
                
            # 提取岗位URL
            job_urls = [meta.get('job_url', '') for meta in results['metadatas'][0][:10]]
            job_urls = [url for url in job_urls if url]  # 过滤空URL
            
            if not job_urls:
                print(f"无有效岗位链接: {name}")
                continue
            
            # 构建短信内容
            content = f"亲爱的毕业生同学{name}：\n" \
                     f"您好！为帮助大家提高应聘成功率，精准瞄准应聘岗位，学校根据同学们在就业信息网填写的简历，" \
                     f"与企业岗位需求进行精准匹配，已为您筛选出{len(job_urls)}个适配度高的岗位。点击下方链接，即可查看岗位详情：\n"
            
            for i, url in enumerate(job_urls, 1):
                content += f"岗位{i}：{url}\n"
            
            content += f"\n这些推荐岗位会随您简历完善、内容更新及新岗位发布而变化。" \
                     f"建议您定期查收短信或关注学校就业信息网、“深技大就业”公众号、学院通知等相关通知，以免错过合适机会。\n\n" \
                     f"深圳技术大学学生就业指导中心\n" \
                     f"{date_str}"
            
            print(f"短信内容长度: {len(content)}")
            
            messages_data.append({
                "name": name,
                "mobile": mobile,
                "content": content
            })
        
        if not messages_data:
            return "没有需要发送的短信数据"
            
        # 批量发送短信
        print(f"准备发送 {len(messages_data)} 条短信")
        result = send_batch_messages(messages_data)
        print(f"发送结果: {result}")
        
        if not result:
            return "发送失败：未收到发送结果"
            
        return f"发送完成！成功：{result['success']}条，失败：{result['fail']}条\n" \
               f"总计尝试发送：{len(messages_data)}条"
               
    except Exception as e:
        print(f"发送异常: {str(e)}")
        import traceback
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

# 创建Gradio界面
with gr.Blocks(title="润小职Agent青春版",theme=gr.themes.Soft(), ) as demo:
    gr.Markdown("## 润小职Agent青春版")
    
    with gr.Tab("添加简历"):
        gr.Markdown("### 方式一：单个添加")
        with gr.Row():
            name_input = gr.Textbox(label="学生姓名")
            stu_id_input = gr.Textbox(label="学号")
        resume_content = gr.Textbox(label="简历内容", lines=10)
        add_btn = gr.Button("添加简历")
        add_output = gr.Textbox(label="添加结果")
        add_btn.click(add_resume_ui, 
                     inputs=[name_input, stu_id_input, resume_content],
                     outputs=add_output)
        
        gr.Markdown("### 方式二：批量导入")
        with gr.Row():
            resume_file_input = gr.File(label="上传JSON文件", file_types=[".json"])
            resume_upload_output = gr.Textbox(label="导入结果")
        resume_file_input.change(handle_resume_json_upload,
                               inputs=[resume_file_input],
                               outputs=resume_upload_output)
    
    with gr.Tab("删除简历"):
        delete_stu_id = gr.Textbox(label="要删除的学号")
        delete_btn = gr.Button("删除简历")
        delete_output = gr.Textbox(label="删除结果")
        delete_btn.click(delete_resume_ui, 
                        inputs=delete_stu_id,
                        outputs=delete_output)
    
    with gr.Tab("查询简历"):
        query_stu_id = gr.Textbox(label="要查询的学号")
        query_btn = gr.Button("查询简历")
        query_output = gr.Textbox(label="查询结果", lines=10)
        query_btn.click(query_resume_ui,
                       inputs=query_stu_id,
                       outputs=query_output)
    
    with gr.Tab("岗位->简历匹配"):
        with gr.Row():
            job_company_name = gr.Textbox(label="公司名称")
            job_id_input = gr.Textbox(label="岗位ID")
        with gr.Row():
            job_major = gr.Textbox(label="专业要求")
            job_url_input = gr.Textbox(label="岗位链接", value="")
        job_requirements = gr.Textbox(label="岗位要求", lines=5)
        job_responsibilities = gr.Textbox(label="岗位职责", lines=5)
        match_resumes_btn = gr.Button("匹配简历")
        match_resumes_output = gr.Textbox(label="匹配结果", lines=20)
        match_resumes_btn.click(search_similar_resumes_by_job,
                            inputs=[job_company_name, job_id_input, job_requirements, 
                                    job_responsibilities, job_major, job_url_input],
                            outputs=match_resumes_output)
    
    with gr.Tab("添加岗位"):
        gr.Markdown("### 方式一：单个添加")
        with gr.Row():
            company_name = gr.Textbox(label="公司名称")
            job_id = gr.Textbox(label="岗位ID")
        with gr.Row():
            major = gr.Textbox(label="专业要求")
            job_url = gr.Textbox(label="岗位链接")
        requirements = gr.Textbox(label="岗位要求", lines=5)
        responsibilities = gr.Textbox(label="岗位职责", lines=5)
        add_job_btn = gr.Button("添加岗位")
        add_job_output = gr.Textbox(label="添加结果")
        add_job_btn.click(add_job_ui,
                         inputs=[company_name, job_id, major, job_url, requirements, responsibilities],
                         outputs=add_job_output)
        
        gr.Markdown("### 方式二：批量导入")
        with gr.Row():
            job_file_input = gr.File(label="上传JSON文件", file_types=[".json"])
            job_upload_output = gr.Textbox(label="导入结果")
        job_file_input.change(handle_job_json_upload,
                            inputs=[job_file_input],
                            outputs=job_upload_output)
    
    with gr.Tab("删除岗位"):
        delete_job_id = gr.Textbox(label="要删除的岗位ID")
        delete_job_btn = gr.Button("删除岗位")
        delete_job_output = gr.Textbox(label="删除结果")
        delete_job_btn.click(delete_job_ui,
                           inputs=delete_job_id,
                           outputs=delete_job_output)
    
    with gr.Tab("查询岗位"):
        query_job_id = gr.Textbox(label="要查询的岗位ID")
        query_job_btn = gr.Button("查询岗位")
        query_job_output = gr.Textbox(label="查询结果", lines=10)
        query_job_btn.click(query_job_ui,
                          inputs=query_job_id,
                          outputs=query_job_output)
    

            
    with gr.Tab("简历->岗位匹配"):
        with gr.Row():
            resume_name = gr.Textbox(label="学生姓名")
            resume_id = gr.Textbox(label="学号")
        resume_text = gr.Textbox(label="简历内容", lines=10)
        match_btn = gr.Button("匹配岗位")
        match_output = gr.Textbox(label="匹配结果", lines=20)
        match_btn.click(search_similar_jobs_by_resume,
                   inputs=[resume_name, resume_id, resume_text],
                   outputs=match_output)
        
    with gr.Tab("发送岗位推荐"):
        gr.Markdown("### 批量发送岗位推荐短信")
        gr.Markdown("请上传包含学生信息的JSON文件，格式为：\n```json\n[\n  {\n    \"name\": \"张三\",\n    "
                   "\"stu_id\": \"202100000001\",\n    \"mobile\": \"13800138000\",\n    "
                   "\"resume_content\": \"简历内容...\"\n  }\n]\n```")
        with gr.Row():
            sms_file_input = gr.File(label="上传学生信息JSON文件", file_types=[".json"])
            sms_output = gr.Textbox(label="发送结果")
        sms_file_input.change(send_job_recommendations_sms,
                            inputs=[sms_file_input],
                            outputs=sms_output)
        



if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860,share=True)
