from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 无论我们在终端的哪个目录下敲回车运行 Python，只要动态向上退 3 层，就一定能绝对定位到整个项目根目录的大门！
# backend/app/config.py (自身) -> app (退1层) -> backend (退2层) -> root (退3层)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"

class Settings(BaseSettings):
    # 如果这些变量在环境变量或 .env 中找不到，Pydantic 会在此文件被导入的瞬间当场抛出异常，拒绝启动。
    OPENROUTER_API_KEY: str
    DATABASE_URL: str
    
    # 精准锁定绝对路径
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH), 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

# 实例化一个单例模式的全局配置对象
settings = Settings()
