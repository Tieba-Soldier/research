from typing import List, Dict, Any
import logging
import time
from app.agents.nodes.learning_path_generator import LearningPathGenerator

logger = logging.getLogger(__name__)


class LearningPathService:
    """学习路径服务：负责学习路径生成"""

    def __init__(self):
        self.generator = LearningPathGenerator()

    async def generate_learning_path(
        self,
        topics: List[Dict[str, Any]],
        resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成学习路径

        Args:
            topics: 主题列表
            resources: 资源列表

        Returns:
            学习路径数据
        """
        start_time = time.time()
        logger.info(f"Generating learning path for {len(topics)} topics and {len(resources)} resources")

        try:
            learning_path = await self.generator.generate(topics, resources)

            duration = time.time() - start_time
            logger.info(f"Learning path generated in {duration:.2f}s")

            return learning_path

        except Exception as e:
            logger.error(f"Learning path generation failed: {str(e)}", exc_info=True)
            # 使用兜底模板
            logger.warning("Using fallback learning path template")
            return self._create_fallback_path(topics, resources)

    def _create_fallback_path(
        self,
        topics: List[Dict[str, Any]],
        resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建兜底学习路径（三阶段固定模板）"""
        topic_names = [
            t.get("normalized") or t.get("normalized_topic") or t.get("raw_text") or ""
            for t in topics
            if (t.get("normalized") or t.get("normalized_topic") or t.get("raw_text"))
        ]
        topic_str = "、".join(topic_names[:3])

        # 按难度分配资源
        basic_resources = [r for r in resources if r.get("difficulty") == "basic"]
        medium_resources = [r for r in resources if r.get("difficulty") == "medium"]
        advanced_resources = [r for r in resources if r.get("difficulty") == "advanced"]

        # 如果没有按难度分类，平均分配
        if not basic_resources and not medium_resources and not advanced_resources:
            third = len(resources) // 3
            basic_resources = resources[:third]
            medium_resources = resources[third:third*2]
            advanced_resources = resources[third*2:]

        def build_stage(
            stage_number: int,
            stage_name: str,
            description: str,
            estimated_hours: int,
            steps: List[Dict[str, Any]]
        ) -> Dict[str, Any]:
            resource_ids = []
            task_titles = []

            for step in steps:
                resource_ids.extend(step.get("resource_ids", []))
                task_titles.append(step.get("title", stage_name))

            return {
                "stage_number": stage_number,
                "stage_name": stage_name,
                "description": description,
                "estimated_hours": estimated_hours,
                "steps": steps,
                "name": stage_name,
                "goal": description,
                "resources": resource_ids,
                "tasks": task_titles,
                "expected_output": f"完成{stage_name}阶段的学习总结或实践结果",
            }

        return {
            "path_name": f"{topic_str}学习路径",
            "description": f"系统性学习{topic_str}的三阶段路径，从基础概念到实践应用",
            "stages": [
                build_stage(
                    1,
                    "基础概念与入门",
                    f"学习{topic_str}的基础知识和核心概念",
                    8,
                    [
                        {
                            "step_number": 1,
                            "title": "理解基础概念",
                            "description": f"学习{topic_str}的基本原理和使用场景",
                            "learning_goals": [
                                f"理解{topic_str}的核心概念",
                                "掌握基本使用方法"
                            ],
                            "resource_ids": [r["id"] for r in basic_resources[:3]],
                            "estimated_minutes": 120
                        },
                        {
                            "step_number": 2,
                            "title": "动手实践",
                            "description": "通过简单示例进行实践练习",
                            "learning_goals": [
                                "完成基础示例",
                                "理解常见用法"
                            ],
                            "resource_ids": [r["id"] for r in basic_resources[3:5]],
                            "estimated_minutes": 120
                        }
                    ]
                ),
                build_stage(
                    2,
                    "深入学习与应用",
                    f"深入学习{topic_str}的高级特性和实际应用",
                    10,
                    [
                        {
                            "step_number": 1,
                            "title": "掌握高级特性",
                            "description": "学习更多高级用法和最佳实践",
                            "learning_goals": [
                                "掌握高级特性",
                                "理解最佳实践"
                            ],
                            "resource_ids": [r["id"] for r in medium_resources[:3]],
                            "estimated_minutes": 180
                        },
                        {
                            "step_number": 2,
                            "title": "实际项目应用",
                            "description": "在实际项目中应用所学知识",
                            "learning_goals": [
                                "完成实际项目",
                                "解决实际问题"
                            ],
                            "resource_ids": [r["id"] for r in medium_resources[3:5]],
                            "estimated_minutes": 180
                        }
                    ]
                ),
                build_stage(
                    3,
                    "进阶与优化",
                    f"掌握{topic_str}的进阶技巧和性能优化",
                    6,
                    [
                        {
                            "step_number": 1,
                            "title": "性能优化",
                            "description": "学习性能优化技巧和调试方法",
                            "learning_goals": [
                                "掌握性能优化方法",
                                "学会问题排查"
                            ],
                            "resource_ids": [r["id"] for r in advanced_resources[:2]],
                            "estimated_minutes": 120
                        },
                        {
                            "step_number": 2,
                            "title": "综合实战",
                            "description": "完成综合性项目，巩固所学知识",
                            "learning_goals": [
                                "完成综合项目",
                                "形成知识体系"
                            ],
                            "resource_ids": [r["id"] for r in advanced_resources[2:4]],
                            "estimated_minutes": 180
                        }
                    ]
                )
            ]
        }
