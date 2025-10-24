from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource, PydanticBaseSettingsSource
from typing import Tuple, Type


class DatabaseSettings(BaseModel):
    """PostgreSQL 数据库配置"""
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    user: str = Field(default="postgres")
    password: str = Field(default="password")
    db: str = Field(default="inforecon")
    
    @property
    def url(self) -> str:
        """生成数据库连接 URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class OpenAISettings(BaseModel):
    """OpenAI API 配置"""
    api_key: str = Field(default="")
    model: str = Field(default="gpt-4")
    base_url: str = Field(default="https://api.openai.com/v1")


class RedisSettings(BaseModel):
    """Redis 配置"""
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: str = Field(default="")
    db: int = Field(default=0)
    
    @property
    def url(self) -> str:
        """生成 Redis 连接 URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    """应用主配置"""
    app_name: str = Field(default="InfoRecon")
    
    # 嵌套配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        case_sensitive=False
    )
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """自定义配置源，添加 TOML 文件支持"""
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls),
            env_settings,
            file_secret_settings,
        )


# 全局配置实例
settings = Settings()

