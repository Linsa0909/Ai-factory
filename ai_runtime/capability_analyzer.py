"""Capability Analyzer — 分析需求来源类型，决定生成前端/后端/全栈"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ProjectType(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULLSTACK = "fullstack"


@dataclass
class DevelopmentPlan:
    project_type: ProjectType
    need_frontend: bool
    need_backend: bool
    need_database: bool
    frontend_framework: str | None
    backend_framework: str | None
    reason: str

    def dag_count(self) -> int:
        return (1 if self.need_frontend else 0) + (1 if self.need_backend else 0)


class CapabilityAnalyzer:
    """分析需求文档的来源格式和内容，决定生成什么类型的项目。

    规则:
    - HTML/Axure/Figma 原型 → 有 UI 描述 → FULLSTACK
    - Markdown/Word/PDF 纯文本需求 → 看内容关键词
    - 纯 API 定义 (OpenAPI/接口文档) → BACKEND
    - 纯 UI 描述 (页面布局/交互) → FRONTEND
    """

    # 前端关键词（出现在需求中说明需要前端）
    FRONTEND_SIGNALS = [
        "页面", "按钮", "表单", "弹窗", "列表", "表格", "导航",
        "侧边栏", "标签", "输入框", "下拉", "拖拽", "画布",
        "page", "button", "form", "modal", "table", "input",
        "sidebar", "tab", "canvas", "drag", "click", "UI",
        "Axure", "Figma", "原型", "prototype", "prototype",
    ]

    # 后端关键词
    BACKEND_SIGNALS = [
        "API", "接口", "endpoint", "数据库", "database",
        "gRPC", "REST", "服务", "service", "后端",
        "CRUD", "增删改查", "鉴权", "auth",
    ]

    # 输入格式强信号
    FORMAT_SIGNALS = {
        ".html": ProjectType.FULLSTACK,   # HTML 原型 = UI + 可能需要后端
        ".htm": ProjectType.FULLSTACK,
    }

    def analyze(self, requirement_path: str, requirement_text: str) -> DevelopmentPlan:
        """分析需求，返回开发计划。"""
        path = Path(requirement_path)
        ext = path.suffix.lower()

        # 1. 格式信号（最强的信号）
        if ext in self.FORMAT_SIGNALS:
            return DevelopmentPlan(
                project_type=self.FORMAT_SIGNALS[ext],
                need_frontend=True,
                need_backend=True,
                need_database=True,
                frontend_framework="React",
                backend_framework="FastAPI",
                reason="HTML/Axure 原型 → 包含 UI 描述，需前后端全栈开发",
            )

        # 2. 内容信号
        text_lower = requirement_text.lower()
        frontend_hits = sum(1 for kw in self.FRONTEND_SIGNALS if kw.lower() in text_lower)
        backend_hits = sum(1 for kw in self.BACKEND_SIGNALS if kw.lower() in text_lower)

        need_fe = frontend_hits >= 2
        need_be = backend_hits >= 1

        if need_fe and need_be:
            return DevelopmentPlan(
                project_type=ProjectType.FULLSTACK,
                need_frontend=True, need_backend=True, need_database=True,
                frontend_framework="React", backend_framework="FastAPI",
                reason=f"检测到 UI 关键词 ({frontend_hits}个) + API 关键词 ({backend_hits}个)",
            )
        elif need_fe:
            return DevelopmentPlan(
                project_type=ProjectType.FRONTEND,
                need_frontend=True, need_backend=False, need_database=False,
                frontend_framework="React", backend_framework=None,
                reason=f"检测到 UI 关键词 ({frontend_hits}个)，纯前端项目",
            )
        else:
            return DevelopmentPlan(
                project_type=ProjectType.BACKEND,
                need_frontend=False, need_backend=True, need_database=True,
                frontend_framework=None, backend_framework="FastAPI",
                reason=f"默认后端项目 (UI:{frontend_hits}, API:{backend_hits})",
            )
