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
import json
from datetime import datetime
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use.agent.memory.views import MemoryConfig
from browser_use.agent.views import (
    REQUIRED_LLM_API_ENV_VARS,
    ActionResult,
    AgentError,
    AgentHistory,
    AgentHistoryList,
    AgentOutput,
    AgentSettings,
    AgentState,
    AgentStepInfo,
    StepMetadata,
    ToolCallingMethod,
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from pydantic import BaseModel, SecretStr
from PyPDF2 import PdfReader

from browser_use import ActionResult, Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

from lmnr import Laminar

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("job_search.log"), logging.StreamHandler()],
)

_project_api_key_b64 = "QTAwRnBDUkZDemRkVXRTSlVLdEdEa3h1ZkxRM0J3QWd3RDhFUzNlU0Y3Q1k5cmIxRXgzRnh0V0paODJvOVcyag=="
project_api_key = base64.b64decode(_project_api_key_b64).decode("utf-8")
print(project_api_key)
Laminar.initialize(project_api_key=project_api_key)
from mem0 import MemoryClient

client = MemoryClient(api_key="m0-DuKNJ68tDM5tmdyJNfERBZFqu5SKgTHKMG3F7hQP")

# 申请记录文件
APPLICATIONS_FILE = "job_applications.csv"
APPLICATION_STATS_FILE = "application_stats.json"

# 确保CSV文件存在
if not os.path.exists(APPLICATIONS_FILE):
    with open(APPLICATIONS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["职位", "公司", "链接", "薪资", "地点", "申请时间"])


# messages = [
#     {
#         "role": "user",
#         "content": "Hi, I'm Alex. I'm a vegetarian and I'm allergic to nuts.",
#     },
#     {
#         "role": "assistant",
#         "content": "Hello Alex! I've noted that you're a vegetarian and have a nut allergy. I'll keep this in mind for any food-related recommendations or discussions.",
#     },
# ]
# client.add(messages, user_id="alex")


logger = logging.getLogger(__name__)
# full screen mode
controller = Controller()

# NOTE: This is the path to your cv file
CV = Path.cwd() / "cv_04_24.pdf"

if not CV.exists():
    raise FileNotFoundError(
        f"You need to set the path to your cv file in the CV variable. CV file not found at {CV}"
    )


class Job(BaseModel):
    title: str
    link: str
    company: str
    fit_score: float
    location: str | None = None
    salary: str | None = None


@controller.action(
    "Save jobs to file - with a score how well it fits to my profile", param_model=Job
)
def save_jobs(job: Job):
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 保存到CSV文件
    with open(APPLICATIONS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [job.title, job.company, job.link, job.salary, job.location, current_time]
        )

    # 更新统计信息
    stats = {"total_applications": 0, "last_update": "", "companies": {}}
    if os.path.exists(APPLICATION_STATS_FILE):
        try:
            with open(APPLICATION_STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except:
            pass

    # 更新统计数据
    stats["total_applications"] += 1
    stats["last_update"] = current_time

    # 更新公司统计
    if job.company not in stats["companies"]:
        stats["companies"][job.company] = 0
    stats["companies"][job.company] += 1

    # 保存统计信息
    with open(APPLICATION_STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    logger.info(f"已保存工作申请: {job.title} at {job.company}")
    return f"已保存工作申请: {job.title} at {job.company} (总计: {stats['total_applications']})"


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
    dom_el = await browser.get_dom_element_by_index(index)

    if dom_el is None:
        return ActionResult(error=f"No element found at index {index}")

    file_upload_dom_el = dom_el.get_file_upload_element()

    if file_upload_dom_el is None:
        logger.info(f"No file upload element found at index {index}")
        return ActionResult(error=f"No file upload element found at index {index}")

    file_upload_el = await browser.get_locate_element(file_upload_dom_el)

    if file_upload_el is None:
        logger.info(f"No file upload element found at index {index}")
        return ActionResult(error=f"No file upload element found at index {index}")

    try:
        await file_upload_el.set_input_files(path)
        msg = f'Successfully uploaded file "{path}" to index {index}'
        logger.info(msg)
        return ActionResult(extracted_content=msg)
    except Exception as e:
        logger.debug(f"Error in set_input_files: {str(e)}")
        return ActionResult(error=f"Failed to upload file to index {index}")


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


browsera = Browser(
    config=BrowserConfig(
        browser_binary_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        disable_security=True,
    )
)


async def main():
    # 检查已申请的工作数量
    total_applications = 0
    if os.path.exists(APPLICATION_STATS_FILE):
        try:
            with open(APPLICATION_STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
                total_applications = stats.get("total_applications", 0)
        except Exception as e:
            logger.error(f"读取申请统计文件时出错: {e}")

    logger.info(f"当前已申请工作数量: {total_applications}/100")

    # 如果已经达到目标，提示用户并退出
    if total_applications >= 100:
        logger.info("✅ 已达到目标申请数量(100)，任务完成！")
        return

    # 基础任务描述
    ground_task = (
        "你是一个专业的求职助手。你的任务是帮助我找工作。以下是你的指导原则："
        "1. 仔细阅读我的简历，了解我的背景和技能。"
        "2. 在LinkedIn等平台上搜索匹配的工作机会。开始第一步是先刷新网页,在输入框中输入 AI agent ,然后点击搜索按钮，search at company in America :"
        "3. 对于每个工作机会，评估它是否与我的技能和职业发展目标相符。"
        "4. 准备并提交求职申请，确保简历和申请表格填写准确。"
        "5. 记录已申请的工作，避免重复申请。"
        "6. 如果遇到任何障碍，灵活调整策略。"
        f"7. 目标是申请100个合适的工作岗位，当前已申请{total_applications}个，还需申请{100-total_applications}个。"
    )

    # 账户信息
    account_profile = (
        "if some website need login,first login in with google : "
        "second use link in page https://www.linkedin.com/in/yixin-zhang-192422ab/"
        "zyxcambridge@gmail.com"
        "yixin zhang "
        "18810901685"
        "location:china shanghai" + "\n"
    )

    # 记忆指令
    memory = (
        "把公司的jd 的主要内容和要求,以及jd的链接都复制下来,保存,然后自己用中文翻译一遍 : "
        + "\n"
    )

    # 行动指令
    action = (
        "增加判断是否陷入了死循环,跳过已经申请的公司,判断一下已经申请了,就跳过,如果已经申请了,就跳过,点击申请相关按钮后,发现100%的进度,说明已经申请了,就跳过 ,记得刷新网页,记录下这个公司的名字,然后跳过: "
        "寻找在网页 上有 【快速申请】的按钮,直接点击【快速申请】,信息直接用已经有的信息,如果没有,使用简历中的信息 : "
        "出现查看您的申请,或者进度出现100%,还差一步,记得滑动页面到最下面,找到提交申请按钮,点击【提交申请】,如果没有,则回去重新找 :   "
        "如果点击申请需要跳转到另外的页面,跳转到公司官网,则点击收藏,暂时放弃,寻找下一个公司,点击【快速申请】,"
        "投递100个公司,才可以停止,如果投递次数少于100次,则回到主页面,重新开始寻找公司,直到找到100个公司为止 :  "
        "如果投递次数大于100次,则停止寻找加拿大州岗位,开始投递 : " + "\n"
        "不要让程序停止，如果任务没有完成就 ，重新在执行一次， 第二次 再次运行任务时，重新打开网页，重新输入，不从之前的断点执行 : "
        "遇到由于页面变更和元素识别问题，则放弃这个页面，点击关闭按钮，回到主页面开始第一步是先刷新网页,在输入框中输入 AI agent ,然后点击搜索按钮，search at company in America。"
        "由于LinkedIn页面的动态特性，该过程速度缓慢且容易出错等问题时"
        "当一个公司申请完成，出现完成按钮时，点击完成按钮，"
        "回到主页面开始第一步是先刷新网页,在输入框中输入 AI agent ,然后点击搜索按钮，search at company in America。"
        "\n"
    )

    # 反思指令
    reflection = (
        "如果失败了，就重新开始，重新打开网页，重新输入，不从之前的断点执行。\n"
        "根据上一次失败的原因，调整策略：\n"
        "1. 如果是CV上传失败，尝试跳过CV上传步骤\n"
        "2. 如果是页面加载问题，等待更长时间\n"
        "3. 如果是表单填写问题，重新尝试\n"
        "4. 如果连续失败3次，切换到下一个职位\n"
        f"5. 记住当前已申请了{total_applications}个工作，目标是100个\n"
    )

    # 组合所有指令
    ground_task = ground_task + memory + account_profile + action + reflection

    # 设置任务列表
    tasks = [
        ground_task + "\n" + "LinkedIn",
        # ground_task + "\n" + "boss直聘",
        # ground_task + "\n" + "猎聘",
    ]

    # 解码API密钥
    _token_b64 = "QUl6YVN5QzV6Q2dYWHdDTmJVbWJRUl9waFJ0bWNpUlNCckNjRHFn"
    token = base64.b64decode(_token_b64).decode("utf-8")
    endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # 初始化模型 gemini-2.5-pro-preview-05-06
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro-preview-05-06", api_key=SecretStr(token)
    )
    planner_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro-preview-05-06", api_key=SecretStr(token)
    )

    # 创建增强的消息上下文
    message_context = (
        f"目标是申请100个合适的工作岗位，当前已申请{total_applications}个，还需申请{100-total_applications}个。"
        "Task completed 之前判断是否完成了100个岗位申请，如果未完成，"
        "Action take_step 出现 Unfinished 时，或者 the agent reached the last step and needs to stop "
        "重新打开linkedin 首页，重新输入AI agent 搜索，不从之前的断点执行。"
        "每完成一个申请，都要使用save_jobs动作记录下来，这样才能正确统计申请数量。"
        "如果页面加载失败或元素无法找到，等待几秒后重试或刷新页面。"
    )

    # 初始化代理
    agent = Agent(
        task=ground_task,
        message_context=message_context,
        llm=model,
        planner_llm=planner_llm,
        use_vision_for_planner=True,
        planner_interval=4,
        controller=controller,
        browser=browsera,
        max_failures=15,  # 增加容错次数
        use_vision=True,
        save_conversation_path="logs/find_apply_jobs",
    )

    # 运行代理，增加最大步骤数
    logger.info("开始运行求职助手...")

    # 连续运行，直到手动停止
    while True:
        try:
            # 不设置max_steps，让agent持续运行
            history = await agent.run()

            # 如果agent完成任务，等待一段时间后继续
            await asyncio.sleep(5)
            logger.info("等待5秒后继续下一轮...")

            # 重置浏览器状态，创建新的上下文
            # await browser.new_context()
            await browsera.close()
            browser = Browser(
                config=BrowserConfig(
                    browser_binary_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    disable_security=True,
                )
            )

            # 重置任务描述和消息上下文
            agent.task = ground_task  # 重置任务描述
            agent.settings.message_context = message_context  # 重置消息上下文
            agent.browser = browser

            # 重置agent状态，准备下一轮
            agent.state.n_steps = 1
            agent.state.consecutive_failures = 0
            agent.state.last_result = []
            agent.state.history = AgentHistoryList(history=[])
            agent.state.last_plan = None
            agent.state.paused = False
            agent.state.stopped = False
            agent.state.message_manager_state = MessageManagerState()

        except Exception as e:
            logger.error(f"发生错误: {str(e)}")
            # 如果发生错误，等待一段时间后继续
            await asyncio.sleep(5)
            logger.info("等待5秒后继续下一轮...")
            continue

        # 检查是否需要停止
        if agent.state.stopped:
            logger.info("Agent已停止，退出循环")
            break

        # 如果达到最大失败次数，重置失败计数
        if agent.state.consecutive_failures >= agent.settings.max_failures:
            logger.warning(
                f"达到最大失败次数({agent.settings.max_failures})，重置失败计数继续运行"
            )
            agent.state.consecutive_failures = 0
            await asyncio.sleep(5)
            continue

    # 获取最新的申请数量
    new_total_applications = total_applications
    if os.path.exists(APPLICATION_STATS_FILE):
        try:
            with open(APPLICATION_STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
                new_total_applications = stats.get("total_applications", 0)
        except Exception as e:
            logger.error(f"读取申请统计文件时出错: {e}")

    # 计算本次新增的申请数量
    new_applications = new_total_applications - total_applications
    logger.info(
        f"本次运行新增了{new_applications}个申请，当前总计: {new_total_applications}/100"
    )

    # 记录其他有用信息
    logger.info(f"访问的URL数量: {len(history.urls())}")
    logger.info(f"截图数量: {len(history.screenshots())}")
    logger.info(f"执行的动作数量: {len(history.action_names())}")
    logger.info(f"错误数量: {len(history.errors())}")

    # 返回历史记录
    return history


if __name__ == "__main__":
    asyncio.run(main())
