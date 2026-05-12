"""
结果质量验证器
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ResultValidator:
    """验证推荐结果的质量"""

    @staticmethod
    def validate_topics(topics: List[Dict[str, Any]]) -> List[str]:
        """验证主题质量"""
        issues = []

        if not topics:
            issues.append("主题列表为空")
            return issues

        for i, topic in enumerate(topics):
            if not topic.get("normalized", "").strip():
                issues.append(f"主题[{i}]的normalized字段为空")
            if not topic.get("keywords"):
                issues.append(f"主题[{i}]的keywords字段为空")

        return issues

    @staticmethod
    def validate_resources(resources: List[Dict[str, Any]]) -> List[str]:
        """验证资源质量"""
        issues = []

        if not resources:
            issues.append("资源列表为空")
            return issues

        for i, resource in enumerate(resources):
            # 必填字段检查
            if not resource.get("title", "").strip():
                issues.append(f"资源[{i}]的title字段为空")
            if not resource.get("url", "").strip():
                issues.append(f"资源[{i}]的url字段为空")
            if not resource.get("summary", "").strip():
                issues.append(f"资源[{i}]的summary字段为空")
            if not resource.get("reason", "").strip():
                issues.append(f"资源[{i}]的reason字段为空")

            # 评分检查
            final_score = resource.get("final_score", 0)
            if final_score <= 0:
                issues.append(f"资源[{i}]的final_score无效: {final_score}")

        return issues

    @staticmethod
    def validate_learning_path(learning_path: Dict[str, Any]) -> List[str]:
        """验证学习路径质量"""
        issues = []

        if not learning_path:
            issues.append("学习路径为空")
            return issues

        stages = learning_path.get("stages", [])
        if not stages:
            issues.append("学习路径的stages字段为空")
            return issues

        for i, stage in enumerate(stages):
            if not stage.get("stage_name", "").strip():
                issues.append(f"学习路径阶段[{i}]的stage_name为空")
            if not stage.get("steps"):
                issues.append(f"学习路径阶段[{i}]的steps为空")

        return issues

    @staticmethod
    def validate_practice_tasks(practice_tasks: List[Dict[str, Any]]) -> List[str]:
        """验证练习任务质量"""
        issues = []

        if not practice_tasks:
            issues.append("练习任务列表为空")
            return issues

        for i, task in enumerate(practice_tasks):
            if not task.get("task_text", "").strip():
                issues.append(f"练习任务[{i}]的task_text字段为空")

        return issues

    @classmethod
    def validate_all(
        cls,
        topics: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        learning_path: Dict[str, Any],
        practice_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """验证所有结果"""
        all_issues = []

        topic_issues = cls.validate_topics(topics)
        resource_issues = cls.validate_resources(resources)
        path_issues = cls.validate_learning_path(learning_path)
        task_issues = cls.validate_practice_tasks(practice_tasks)

        all_issues.extend(topic_issues)
        all_issues.extend(resource_issues)
        all_issues.extend(path_issues)
        all_issues.extend(task_issues)

        is_valid = len(all_issues) == 0

        result = {
            "is_valid": is_valid,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "summary": {
                "topics_count": len(topics),
                "resources_count": len(resources),
                "has_learning_path": learning_path is not None,
                "practice_tasks_count": len(practice_tasks),
                "topic_issues": len(topic_issues),
                "resource_issues": len(resource_issues),
                "path_issues": len(path_issues),
                "task_issues": len(task_issues)
            }
        }

        if not is_valid:
            logger.warning(f"质量验证失败: {len(all_issues)}个问题")
            for issue in all_issues[:5]:  # 只记录前5个
                logger.warning(f"  - {issue}")
        else:
            logger.info("质量验证通过")

        return result
