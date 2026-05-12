"""
LLM节点的fallback机制
当LLM调用或解析失败时，提供默认输出
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class LLMFallback:
    """LLM节点fallback生成器"""

    @staticmethod
    def user_need_analysis(user_input: str) -> Dict[str, Any]:
        """用户需求分析fallback"""
        logger.warning(f"Using fallback for UserNeedAnalyzer")
        return {
            "user_level": "初学者",
            "learning_goal": f"学习{user_input}相关知识",
            "time_constraint": "中等时间投入",
            "preferred_format": "视频和文章结合"
        }

    @staticmethod
    def topic_extraction(user_input: str) -> Dict[str, Any]:
        """主题提取fallback"""
        logger.warning(f"Using fallback for TopicExtractor")
        # 简单分词，取前3个关键词作为主题
        keywords = user_input.replace('、', ' ').replace('，', ' ').replace(',', ' ').split()[:3]
        if not keywords:
            keywords = [user_input[:20]]

        topics = [
            {
                "raw_text": kw,
                "normalized_topic": kw,
                "priority": 10 - i
            }
            for i, kw in enumerate(keywords)
        ]
        return {"topics": topics, "main_topic": keywords[0]}

    @staticmethod
    def resource_evaluation(tavily_results: List[Dict], topic: str) -> Dict[str, Any]:
        """资源评估fallback"""
        logger.warning(f"Using fallback for ResourceEvaluator: {topic}")

        resources = []
        for i, result in enumerate(tavily_results[:5]):
            title = result.get("title", f"资源{i+1}")
            url = result.get("url", "")
            content = result.get("content", "") or result.get("snippet", "")

            resources.append({
                "title": title if title else f"资源{i+1}",
                "url": url if url else f"https://www.google.com/search?q={topic}",
                "summary": content[:150] if content else f"关于{topic}的学习资源",
                "reason": f"与{topic}相关的学习资源",
                "quality_score": 7,
                "difficulty_level": "中等"
            })

        if not resources:
            # 如果没有Tavily结果，生成一个默认资源
            resources.append({
                "title": f"{topic}学习资源",
                "url": f"https://www.google.com/search?q={topic}",
                "summary": f"关于{topic}的搜索结果",
                "reason": "推荐通过搜索引擎查找相关资源",
                "quality_score": 5,
                "difficulty_level": "中等"
            })

        return {"resources": resources}

    @staticmethod
    def learning_path(topics: List[str], resources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """学习路径fallback"""
        logger.warning(f"Using fallback for LearningPathGenerator")

        topic_str = "、".join(topics[:3]) if topics else "学习主题"
        resources = resources or []

        def stage_payload(index: int, stage_name: str, description: str, estimated_hours: int) -> Dict[str, Any]:
            stage_resources = resources[index::3]
            resource_ids = [resource.get("id") for resource in stage_resources if resource.get("id") is not None]
            task_titles = [
                resource.get("title", f"{stage_name}任务{i + 1}")
                for i, resource in enumerate(stage_resources[:3])
            ] or [f"围绕{stage_name}完成一次学习与总结"]

            return {
                "stage_number": index + 1,
                "stage_name": stage_name,
                "description": description,
                "estimated_hours": estimated_hours,
                "steps": [
                    {
                        "step_number": 1,
                        "title": stage_name,
                        "description": description,
                        "learning_goals": [description],
                        "resource_ids": resource_ids,
                        "estimated_minutes": estimated_hours * 60,
                    }
                ],
                "name": stage_name,
                "goal": description,
                "resources": resource_ids,
                "tasks": task_titles,
                "expected_output": f"完成{stage_name}阶段的学习总结或实践记录",
            }

        stages = [
            stage_payload(0, "基础入门", f"学习{topic_str}的基础概念和核心原理，建立知识框架。", 5),
            stage_payload(1, "深入理解", f"深入理解{topic_str}的原理和应用场景，掌握常见问题的解决方案。", 8),
            stage_payload(2, "实践应用", f"通过项目实践巩固{topic_str}知识，学习生产环境的最佳实践。", 7),
        ]

        return {
            "path_name": f"{topic_str}学习路径",
            "description": f"围绕{topic_str}构建的三阶段学习路径。",
            "stages": stages,
        }

    @staticmethod
    def practice_tasks(topic: str) -> Dict[str, Any]:
        """练习任务fallback"""
        logger.warning(f"Using fallback for PracticeTaskGenerator: {topic}")

        tasks = [
            {
                "task_text": f"请解释{topic}的核心概念，包括其定义、特点和应用场景。",
                "difficulty": "简单",
                "estimated_time": "1小时"
            },
            {
                "task_text": f"编写代码实现{topic}的基本功能，要求实现核心逻辑并添加必要的注释。",
                "difficulty": "中等",
                "estimated_time": "3小时"
            },
            {
                "task_text": f"分析在生产环境中使用{topic}可能遇到的问题，并提出解决方案。",
                "difficulty": "困难",
                "estimated_time": "4小时"
            }
        ]

        return {"tasks": tasks}
