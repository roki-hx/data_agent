import os

from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

# 加载项目根目录 .env 文件中的环境变量
# load_dotenv()

llm = init_chat_model(
    model=app_config.llm.model_name,
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    # base_url="",
    temperature=0 # 让大型处理的结果稳定，不要创意
)

# llm = init_chat_model(
#     model="qwen3.7-plus",
#     model_provider="openai",
#     api_key= os.getenv("DASHSCOPE_API_KEY"),
#     base_url=os.getenv("DASHSCOPE_BASE_URL"),
#
#     temperature=0 # 让大型处理的结果稳定，不要创意
# )

if __name__ == '__main__':
    for chunk in llm.stream("2026年11月1日是星期几"):
        print(chunk.text, end="", flush=True)
