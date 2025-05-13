import os
import base64
import asyncio
import logging
from pathlib import Path
from pydantic import BaseModel, SecretStr
from PyPDF2 import PdfReader

from dotenv import load_dotenv
from browser_use import Agent, Controller, ActionResult
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext
from langchain_google_genai import ChatGoogleGenerativeAI

# 日志配置
logger = logging.getLogger(__name__)

# 初始化控制器和浏览器
controller = Controller()
browser = Browser(
    config=BrowserConfig(
        browser_binary_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        disable_security=True,
    )
)

# 环境变量
_project_api_key_b64 = "QTAwRnBDUkZDemRkVXRTSlVLdEdEa3h1ZkxRM0J3QWd3RDhFUzNlU0Y3Q1k5cmIxRXgzRnh0V0paODJvOVcyag=="
project_api_key = base64.b64decode(_project_api_key_b64).decode("utf-8")
print("Project Key Loaded")

# 设置B超单PDF路径
ULTRASOUND_REPORT = Path("./ultrasound_report.pdf")

# 构建分析任务
instruction = (
    "你是产科专家。请根据上传的B超单内容判断是否存在早产风险。"
    "判断指标包括：宫颈长度（小于25mm为高风险）、孕周是否早于37周，是否存在子宫收缩、羊水异常等信息。"
    "请总结关键数值，做出早产风险等级判断（高风险/中风险/低风险），并提供建议。"
)


import os
import sys

from dotenv import load_dotenv
from pydantic import SecretStr

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig


browser = Browser(
    config=BrowserConfig(
        headless=False,
        cdp_url="http://localhost:9222",
    )
)
controller = Controller()

_token_b64 = "QUl6YVN5QzV6Q2dYWHdDTmJVbWJRUl9waFJ0bWNpUlNCckNjRHFn"
token = base64.b64decode(_token_b64).decode("utf-8")
endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/"
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=SecretStr(token))
planner_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro-preview-03-25", api_key=SecretStr(token)
)


async def main():
    task = instruction + " 从医疗杂志和医疗学术杂志搜索信息 \n - Magnus"
    task += " and save the document as pdf"

    agent = Agent(
        task=task,
        llm=model,
        controller=controller,
        browser=browser,
    )

    await agent.run()
    await browser.close()

    input("Press Enter to close...")


if __name__ == "__main__":
    asyncio.run(main())
