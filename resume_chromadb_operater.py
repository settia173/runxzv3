# -*- coding: utf-8 -*-
from chromadb.utils import embedding_functions  
import chromadb
import json
import re

# 创建 BGE 中文嵌入模型实例
bge_embedding = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-large-zh-v1.5"
)

# 连接到已有的 ChromaDB collection
client = chromadb.PersistentClient(path="./local_resumes_chromaDB")
collection = client.get_collection(
    name="resumes",
    embedding_function=bge_embedding
)

def add_resume(resume_data):
    """添加简历到数据库"""
    text = resume_data.get('resume_content', '')
     # 提取电话号码
    phone_pattern = r'1[3-9]\d{9}'
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group() if phone_match else ''
    # 元数据
    resume_metadata = {
        "name": resume_data.get("name", ""),
        "stu_id": resume_data.get("stu_ids", ""),
        "mobiles": phone
    }
    
    # 将ID转换为字符串
    stu_id = str(resume_data.get("stu_ids", ""))
    
    # 添加到collection
    if text.strip():
        try:
            collection.add(
                documents=[text],
                metadatas=[resume_metadata], 
                ids=[stu_id]
            )
            return True
        except Exception as e:
            print(f"添加简历失败: {e}")
            return False

def delete_resume(stu_id):
    """根据学号删除简历"""
    try:
        collection.delete(ids=[str(stu_id)])
        return True
    except Exception as e:
        print(f"删除简历失败: {e}")
        return False

def query_resume(stu_id):
    """根据学号查询简历"""
    try:
        result = collection.get(
            ids=[str(stu_id)],
            include=['metadatas', 'documents']
        )
        
        if result['metadatas'] and result['documents']:
            return {
                'metadata': result['metadatas'][0],
                'content': result['documents'][0]
            }
        return None
    except Exception as e:
        print(f"查询简历失败: {e}")
        return None

def similarity_search(query_text, n_results=5):
    """相似度搜索"""
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=['metadatas', 'documents', 'distances']
        )
        return results
    except Exception as e:
        print(f"相似度搜索失败: {e}")
        return None
def batch_add_resumes(resumes_datas):
    """批量添加简历信息
    Args:
        resumes_datas: 简历数据列表
        格式: [{"name": str, "stu_ids": str, "resume_content": str}, ...]
    Returns:
        int: 成功添加的简历数量
    """
    success_count = 0
    try:
        print(f"开始处理 {len(resumes_datas)} 条简历数据")
        
        for resume in resumes_datas:
            # 直接使用原始字段名，不需要转换
            if all(key in resume for key in ["name", "stu_ids", "resume_content"]):
                if add_resume(resume):
                    success_count += 1
                else:
                    print(f"添加失败 - 姓名: {resume.get('name')}, 学号: {resume.get('stu_ids')}")
            else:
                print(f"数据格式错误 - 当前keys: {resume.keys()}")
                
        print(f"成功添加: {success_count}/{len(resumes_datas)}")
        
    except Exception as e:
        print(f"批量添加过程出错: {str(e)}")
        
    return success_count

if __name__ == "__main__":
    # 测试添加
    #test_resume = {"name": "张三","stu_ids": "66","resume_content": "简历信息 基本信息 - 姓名：张三 - 性别：男 - 年龄：24岁 - 电话：15873049129 - 邮箱：1466717255@qq.com - 地址：贵州省德江县 意向岗位 - 职位：全职 - 地点：深圳 - 行业：电力、热力、燃气及水生产和供应业 - 薪资：7k-12k 教育经历 - 时间：2021-09至2025-06 - 学校：深圳技术大学 - 专业：集成电路与光电芯片 - 学历：本科 专业技能 - 语言：掌握C/C++，Python，Verilog等编程语言，获得大学生英语四、六级证书 - 软件：熟练掌握Quartus，ModelSim，Vivado，Solid words，Excel等软件 工作经历 - 时间：2023-08至2024-01 - 公司：中国科学院深圳先进技术研究院 - 职位：实习生 - 描述：实习期间跟随导师参与“可穿戴设备及人体血液动力学”项目研究，主要负责通过编程（Fortran 95语言）和计算机仿真进行人体血液动力学模型的建立、仿真，次要负责对可穿戴设备（检测人体健康指标探针等）进行组装、搭建 项目经历 - 时间：2023-03至2025-06 - 项目：轻量级RISC-V处理器设计、数字综合和验证 - 描述：深圳技术大学高级项目 - 描述：精简指令集计算机架构研究，组合逻辑与时序逻辑电路设计、仿真，简易处理器的搭建 - 描述：通过学习并掌握相应verilog语言代码对数字芯片进行时序逻辑仿真 - 时间：2023-07至2023-09 - 项目：基于fpga实现手势识别开发 - 描述：深圳技术大学 - 描述：基于fpga开发板进行嵌入式开发，利用vivado软件编程实现图像边缘检测，二值化处理与神经网络模型搭建 - 描述：主要负责调试fpga开发板与神经网络模型的选取、搭建以及调参 校内荣誉 - 时间：2023-09 - 奖项：集成电路与光电芯片学院“研究与创新”奖 - 时间：2023-09 - 奖项：集成电路与光电芯片学院“工匠之星”三等奖 - 时间：2023-08 - 奖项：《中国软件杯大学生软件设计大赛》区域赛三等奖 - 时间：2022-06 - 奖项：集成电路与光电芯片学院工匠之星三等奖 - 时间：2022-03 - 奖项：美国大学生数学建模比赛MCM国际三等奖 校内职务 - 时间：2022-09至2023-02 - 职务：心理社副社长 - 描述：负责管理与组织社团内外活动，曾多次成功举办校内大型心理健康活动 - 时间：2023-02至2023-12 - 职务：智能赛车车队摄影师 - 描述：负责会议记录，拍摄比赛过程 主修课程 - 模拟电子技术 - 数字电子技术 - 半导体物理与器件 - EDA技术与应用实践 - 集成电路制备工艺 - 工程制图及CAD - 通信原理 - 数字信号处理 - 模拟集成电路版图设计"}
    #print("添加测试:", add_resume(test_resume))
    
    # 测试查询
    
    print("查询测试:", query_resume("67"))
    # 测试相似度搜索
   
    
    # 测试删除
    #print("删除测试:", delete_resume("66"))