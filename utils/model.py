import os
import base64
import requests
from openai import OpenAI
from typing import List, Dict, Any
import time

# ====================== 这里补上缺失的常量 ======================
API_KEY = "your_api_key"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
# ===============================================================

class LVMChat:
    """多模态大模型聊天类"""
    def __init__(self, api_key: str = API_KEY, base_url: str = BASE_URL, model: str = "glm-4.6v-flash"):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.conversation_history = []

    def _encode_image(self, image_path: str) -> str:
        """将本地图片编码为 Base64"""
        with open(image_path, "rb") as image_file:
            base64_str = base64.b64encode(image_file.read()).decode('utf-8')
        
        return f"data:image/jpeg;base64,{base64_str}"

    def get_multimodal_response(self, text: str, image_path: str, use_history: bool = False, res_format: str = None) -> str:
        """
        获取多模态响应
        :param text: 提问文本
        :param image_path: 本地图片路径
        :param use_history: 是否使用历史对话记录
        """
        # 编码图片
        image_base64 = self._encode_image(image_path)
        current_messages={
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_base64}  
                        }
                    ]
                }
        if use_history:
            message = self.conversation_history + [current_messages]

        # 发送请求
        if res_format == "json":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                temperature=0.7,
                response_format = {"type": "json_object"}
        )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                temperature=0.7
            )
        result = response.choices[0].message.content
        
        # 如果开启了使用历史对话记录，将当前对话记录添加到历史记录中
        if use_history:
            self.conversation_history.append(current_messages)
            self.conversation_history.append({"role": "assistant", "content": result})

        return result

    def clear_history(self):
        """清除历史对话记录"""
        self.conversation_history = []



if __name__ == "__main__":
    # 初始化
    lvchat = LVChat(model="glm-4.6v-flashx")

    # 本地图片路径（Windows 路径）
    img_path = r"D:\Epan\GUI_agent_demo\image\myimage.jpg"

    # 提问
    response = lvchat.get_multimodal_response("这张图片是讲什么的", img_path, use_history=True)
    print(response)
    response = lvchat.get_multimodal_response("你刚刚说了什么，再说一次", img_path, use_history=True)
    print(response)

