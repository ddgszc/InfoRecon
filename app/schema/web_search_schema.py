from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime



class WebSearchInfo(BaseModel):
    """Web搜索结果信息"""
    query: str = Field(description="搜索查询关键词")
    search_result: str = Field(default="", description="搜索结果内容")
    search_time: datetime = Field(default_factory=datetime.now, description="搜索时间")
    error: Optional[str] = Field(default=None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Python编程",
                "search_result": "Python是一种编程语言...",
                "search_time": "2024-01-01T12:00:00"
            }
        }

