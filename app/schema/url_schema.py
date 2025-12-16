from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class URLAnalysisInfo(BaseModel):
    """URL分析结果信息"""
    url: str = Field(description="分析的URL地址")
    url_content: str = Field(default="", description="URL页面内容（Markdown格式）")
    redirect_chain: List[str] = Field(default_factory=list, description="URL重定向链路")
    analysis_time: datetime = Field(default_factory=datetime.now, description="分析时间")
    error: Optional[str] = Field(default=None, description="错误信息")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com",
                "url_content": "# Example Domain\n\nThis domain is for use in illustrative examples...",
                "redirect_chain": ["https://example.com"],
                "analysis_time": "2024-01-01T12:00:00"
            }
        }
    )

