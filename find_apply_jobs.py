"""
coding=utf-8
Try demos in the example library with uv run examples/simple.py
Run the linter/formatter with uv run ruff format examples/some/file.py
Run tests with uv run pytest
Build the package with uv build
"""

import asyncio
import csv
import logging
import os
import base64
import sys
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, SecretStr
from PyPDF2 import PdfReader

from browser_use import ActionResult, Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

from lmnr import Laminar

_project_api_key_b64 = "QTAwRnBDUkZDemRkVXRTSlVLdEdEa3h1ZkxRM0J3QWd3RDhFUzNlU0Y3Q1k5cmIxRXgzRnh0V0paODJvOVcyag=="
project_api_key = base64.b64decode(_project_api_key_b64).decode("utf-8")
print(project_api_key)
Laminar.initialize(project_api_key=project_api_key)

logger = logging.getLogger(__name__)
# full screen mode
controller = Controller()

# NOTE: This is the path to your cv file


class Job(BaseModel):
    title: str
    link: str
    company: str
    fit_score: float
    location: str | None = None
    salary: str | None = None
    applied: bool = False
    application_date: str | None = None


@controller.action(
    "Save jobs to file - with a score how well it fits to my profile", param_model=Job
)
def save_jobs(job: Job):
    from datetime import datetime

    if job.applied and not job.application_date:
        job.application_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("jobs.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                job.title,
                job.company,
                job.link,
                job.salary,
                job.location,
                job.applied,
                job.application_date,
            ]
        )

    return "Saved job to file"


@controller.action("Read jobs from file")
def read_jobs():
    with open("jobs.csv") as f:
        return f.read()


@controller.action("Read my cv for context to fill forms")
def read_cv():
    pdf = PdfReader(CV)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() or ""
    logger.info(f"Read cv with {len(text)} characters")
    return ActionResult(extracted_content=text, include_in_memory=True)


@controller.action(
    "Upload cv to element - call this function to upload if element is not found, try with different index of the same upload element",
)
async def upload_cv(index: int, browser: BrowserContext):
    path = str(CV.absolute())

    # Use existing file upload controller action
    return await controller.execute_action(
        "upload_file", {"index": index, "file_path": path}
    )


@controller.action(
    "Upload profile picture to element",
)
async def upload_profile_picture(index: int, browser: BrowserContext):
    # Use specific image file in current directory
    path = os.path.join(os.getcwd(), "zhangyixin-touxiang.png")

    # Validate file exists
    if not os.path.exists(path):
        return ActionResult(error=f"Image file not found: {path}", is_done=True)

    # Validate image file type
    valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    _, ext = os.path.splitext(path.lower())

    if ext not in valid_extensions:
        return ActionResult(
            error=f"Invalid image file extension: {ext}. Must be one of {valid_extensions}",
            is_done=True,
        )

    # Use existing file upload controller action
    return await controller.execute_action(
        "upload_file", {"index": index, "file_path": path}
    )

    # browser = Browser(
    #     config=BrowserConfig(
    #         browser_binary_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    #         disable_security=True,
    #     )
    # )


# config = BrowserConfig(
#     browser_binary_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
#     disable_security=False,
# )

# config = BrowserConfig(
#     # Specify the path to your Chrome executable
#     browser_binary_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS path
#     # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
#     # For Linux, typically: '/usr/bin/google-chrome'
# )

# "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222  --user-data-dir=/Users/yixin0909zhang/chrome-debug --no-first-run --no-default-browser-check
#  --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
# --no-first-run --no-default-browser-check
# Configure browser to connect to local Chrome instance in debug mode
config = BrowserConfig(
    cdp_url="http://localhost:9222",  # Connect to Chrome DevTools Protocol
    disable_security=True,  # Allow automation features
)

# Create browser instance with CDP configuration
browser = Browser(config=config)


def get_job_stats():
    try:
        with open("jobs.csv", "r") as f:
            reader = csv.reader(f)
            jobs = list(reader)
            applied = sum(
                1 for row in jobs if len(row) >= 6 and row[5].lower() == "true"
            )
            total = len(jobs)
            return {
                "applied": applied,
                "total": total,
                "remaining": 100 - applied,
                "success_rate": (applied / total * 100) if total > 0 else 0,
            }
    except FileNotFoundError:
        return {"applied": 0, "total": 0, "remaining": 100, "success_rate": 0}


async def main():
    # Initialize or get current progress
    stats = get_job_stats()
    applied_count = stats["applied"]

    # ground_task = (
    #   'You are a professional job finder. '
    #   '1. Read my cv with read_cv'
    #   '2. Find jobs that match my profile'
    # )
    ground_task = (
        "你是一个专业的求职助手。你的任务是帮助我找工作。以下是你的指导原则："
        "1. 仔细阅读我的简历，了解我的背景和技能。"
        "2. 在LinkedIn等平台上搜索匹配的工作机会。开始第一步是先刷新网页,在输入框中输入 AI agent ,然后点击搜索按钮，search at company in America :"
        "3. 对于每个工作机会，评估它是否与我的技能和职业发展目标相符。"
        "4. 准备并提交求职申请，确保简历和申请表格填写准确。"
        "5. 记录已申请的工作，避免重复申请。"
        "6. 如果遇到任何障碍，灵活调整策略。"
        "7. 目标是申请100个合适的工作岗位。"
    )
    account_profile = (
        "if some website need login,first login in with google : "
        "second use link in page https://www.linkedin.com/in/yixin-zhang-192422ab/"
        "zyxcambridge@gmail.com"
        "yixin zhang "
        "location:china shanghai" + "\n"
    )
    memory = (
        "把公司的jd 的主要内容和要求,以及jd的链接都复制下来,保存,然后自己用中文翻译一遍 : "
        + "\n"
    )

    action = (
        "增加判断是否陷入了死循环,跳过已经申请的公司,判断一下已经申请了,就跳过,如果已经申请了,就跳过,点击申请相关按钮后,发现100%的进度,说明已经申请了,就跳过 ,记得刷新网页,记录下这个公司的名字,然后跳过: "
        "寻找在网页 上有 【快速申请】的按钮,直接点击【快速申请】,信息直接用已经有的信息,如果没有,使用简历中的信息 : "
        "出现查看您的申请,或者进度出现100%,还差一步,记得滑动页面到最下面,找到提交申请按钮,点击【提交申请】,如果没有,则回去重新找 :   "
        "如果点击申请需要跳转到另外的页面,跳转到公司官网,则点击收藏,暂时放弃,寻找下一个公司,点击【快速申请】,"
        "投递100个公司,才可以停止,如果投递次数少于100次,则回到主页面,重新开始寻找公司,直到找到100个公司为止 :  "
        "如果投递次数大于100次,则停止寻找加拿大州岗位,开始投递 : " + "\n"
        "不要让程序停止，如果任务没有完成就 ，重新在执行一次， 第二次 再次运行任务时，重新打开网页，重新输入，不从之前的断点执行 : "
        + "\n"
    )

    # Track previous agent state and reflection
    class AgentState:
        def __init__(self):
            self.last_task = None
            self.last_error = None
            self.consecutive_failures = 0
            self.last_page_url = None
            self.last_action = None

    agent_state = AgentState()

    reflection = (
        "如果失败了，就重新开始，重新打开网页，重新输入，不从之前的断点执行。\n"
        "根据上一次失败的原因，调整策略：\n"
        "1. 如果是CV上传失败，尝试跳过CV上传步骤\n"
        "2. 如果是页面加载问题，等待更长时间\n"
        "3. 如果是表单填写问题，重新尝试\n"
        "4. 如果连续失败3次，切换到下一个职位\n"
    )
    # action = (
    #     "增加判断是否陷入了死循环,跳过已经申请的公司,判断一下是否已经沟通了,就跳过,记得刷新网页,记录下这个公司的名字,然后跳过: "
    #     "每次开始,都重新搜索,jd中要有 ai agent,没有则跳过,选择下一个公司,开始聊天 "
    #     + "\n"
    #     "寻找在网页 上有 【立即沟通】的按钮,直接点击【立即沟通】,信息直接用已经有的信息,如果没有,使用打招呼的信息 : "
    #     + "\n"
    #     "投递100个公司,才可以停止,如果投递次数少于100次,则回到主页面,重新开始寻找公司,直到找到100个公司为止 :  "
    #     + "\n"
    # )
    ground_task = ground_task + memory + account_profile + action + reflection
    tasks = [
        # ground_task + "\n" + "Google",
        # ground_task + "\n" + "Amazon",
        # ground_task + '\n' + 'Apple',
        # ground_task + "\n" + "Microsoft",
        # ground_task + "\n" + "Meta",
        # ground_task + "\n" + "Netflix",
        # ground_task + "\n" + "Salesforce",
        # ground_task + "\n" + "Tiktok",
        # ground_task + "\n" + "Facebook",
        # ground_task + "\n" + "Twitter",
        ground_task + "\n" + "LinkedIn",
        # ground_task + "\n" + "boss直聘",
        # ground_task + "\n" + "猎聘",
        # ground_task + "\n" + "Uber",
        # ground_task + "\n" + "Airbnb",
    ]

    # Store only base64-encoded keys in version control. Do NOT commit plaintext keys.
    _token_b64 = "QUl6YVN5QzV6Q2dYWHdDTmJVbWJRUl9waFJ0bWNpUlNCckNjRHFn"
    token = base64.b64decode(_token_b64).decode("utf-8")
    endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/"
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp", api_key=SecretStr(token)
    )
    planner_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro-preview-03-25", api_key=SecretStr(token)
    )

    max_retries = 3
    retry_delay = 60  # seconds
    stats = get_job_stats()
    applied_count = stats["applied"]

    while applied_count < 100:
        for task in tasks:
            retry_count = 0
            while retry_count < max_retries and applied_count < 100:
                try:
                    # Update task with current progress and stats
                    stats = get_job_stats()
                    applied_count = stats["applied"]
                    progress_info = (
                        f"当前进度：已申请 {stats['applied']}/100 个职位\n"
                        f"总浏览职位数：{stats['total']}\n"
                        f"申请成功率：{stats['success_rate']:.1f}%\n"
                        f"剩余申请数：{stats['remaining']}\n"
                    )
                    task_with_progress = f"{task}\n{progress_info}"

                    # Add reflection if there were previous failures
                    task_with_reflection = task_with_progress
                    if agent_state.last_error:
                        reflection_info = (
                            f"上次失败原因: {agent_state.last_error}\n"
                            f"上次执行任务: {agent_state.last_task}\n"
                            f"连续失败次数: {agent_state.consecutive_failures}\n"
                            f"上次页面URL: {agent_state.last_page_url}\n"
                            f"上次执行动作: {agent_state.last_action}\n"
                            "---反思和调整---\n"
                        )
                        task_with_reflection = (
                            f"{task_with_progress}\n{reflection}\n{reflection_info}"
                        )

                    agent = Agent(
                        task=task_with_reflection,
                        llm=model,
                        planner_llm=planner_llm,
                        use_vision_for_planner=True,
                        planner_interval=4,
                        controller=controller,
                        browser=browser,
                        max_failures=10,
                        use_vision=True,
                    )

                    # Store current state before running
                    agent_state.last_task = task
                    agent_state.last_action = (
                        None  # Will be updated by agent during execution
                    )

                    await agent.run(max_steps=100)
                    # Update stats after successful run
                    stats = get_job_stats()
                    applied_count = stats["applied"]
                    logger.info(f"Progress update: {progress_info}")

                    # Reset state on success
                    agent_state.last_error = None
                    agent_state.consecutive_failures = 0
                    break  # Success, move to next task

                except Exception as e:
                    retry_count += 1
                    agent_state.consecutive_failures += 1
                    agent_state.last_error = str(e)

                    # Try to get current URL if possible
                    try:
                        agent_state.last_page_url = browser.current_url
                    except:
                        agent_state.last_page_url = "Unknown"

                    logger.error(
                        f"Agent failed with error: {e}. "
                        f"Attempt {retry_count}/{max_retries}. "
                        f"Consecutive failures: {agent_state.consecutive_failures}"
                    )

                    if retry_count < max_retries:
                        logger.info(f"Waiting {retry_delay} seconds before retry...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff

                        # If we've failed multiple times, try refreshing the page
                        if agent_state.consecutive_failures >= 2:
                            try:
                                await browser.refresh()
                                logger.info("Refreshed page after multiple failures")
                            except Exception as refresh_error:
                                logger.error(f"Failed to refresh page: {refresh_error}")
                    else:
                        logger.error(
                            f"Max retries reached for task. "
                            f"Total consecutive failures: {agent_state.consecutive_failures}. "
                            f"Moving to next task."
                        )

    final_stats = get_job_stats()
    logger.info(
        f"Job application process completed!\n"
        f"Total jobs applied: {final_stats['applied']}\n"
        f"Total jobs viewed: {final_stats['total']}\n"
        f"Success rate: {final_stats['success_rate']:.1f}%"
    )


if __name__ == "__main__":
    asyncio.run(main())
