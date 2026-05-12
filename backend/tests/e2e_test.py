"""
端到端测试脚本
测试所有API接口并进行质量验证
"""
import requests
import json
import time
from typing import Dict, Any, List


class E2ETestRunner:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []

    def test_create_recommendation(self, user_input: str, test_name: str) -> Dict[str, Any]:
        """测试创建推荐任务"""
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print(f"输入: {user_input}")
        print(f"{'='*60}")

        result = {
            "test_name": test_name,
            "user_input": user_input,
            "success": False,
            "task_id": None,
            "total_duration": 0,
            "topics_count": 0,
            "resources_count": 0,
            "practice_tasks_count": 0,
            "has_learning_path": False,
            "empty_fields": [],
            "cache_hits": 0,
            "error": None
        }

        try:
            # 1. 创建任务
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/recommendations",
                json={"user_input": user_input},
                timeout=60
            )

            if response.status_code != 200:
                result["error"] = f"创建任务失败: {response.status_code}"
                return result

            data = response.json()
            task_id = data["data"]["task_id"]
            result["task_id"] = task_id
            print(f"[OK] 任务创建成功: task_id={task_id}")

            # 2. 轮询任务状态
            max_polls = 60
            poll_interval = 5

            for i in range(max_polls):
                time.sleep(poll_interval)

                status_response = requests.get(
                    f"{self.base_url}/api/recommendations/tasks/{task_id}"
                )

                if status_response.status_code != 200:
                    result["error"] = f"查询状态失败: {status_response.status_code}"
                    return result

                status_data = status_response.json()["data"]
                status = status_data["status"]
                progress = status_data["progress"]

                print(f"  轮询 {i+1}: {status} ({progress}%)")

                if status == "COMPLETED":
                    result["total_duration"] = time.time() - start_time
                    print(f"[OK] 任务完成，总耗时: {result['total_duration']:.2f}s")
                    break
                elif status == "FAILED":
                    result["error"] = f"任务失败: {status_data.get('error_message', 'Unknown')}"
                    return result

            if status != "COMPLETED":
                result["error"] = f"任务超时，最终状态: {status}"
                return result

            # 3. 获取推荐结果
            result_response = requests.get(
                f"{self.base_url}/api/recommendations/tasks/{task_id}/result"
            )

            if result_response.status_code != 200:
                result["error"] = f"获取结果失败: {result_response.status_code}"
                return result

            result_data = result_response.json()["data"]

            # 4. 验证结果质量
            result["topics_count"] = len(result_data["topics"])
            result["resources_count"] = len(result_data["resources"])
            result["practice_tasks_count"] = len(result_data["practice_tasks"])
            result["has_learning_path"] = result_data["learning_path"] is not None

            print(f"\n结果统计:")
            print(f"  主题数: {result['topics_count']}")
            print(f"  资源数: {result['resources_count']}")
            print(f"  练习任务数: {result['practice_tasks_count']}")
            print(f"  学习路径: {'有' if result['has_learning_path'] else '无'}")

            # 5. 检查空字段
            empty_fields = self._check_empty_fields(result_data)
            result["empty_fields"] = empty_fields

            if empty_fields:
                print(f"\n[WARN] 发现空字段:")
                for field in empty_fields:
                    print(f"  - {field}")
            else:
                print(f"\n[OK] 无空字段")

            # 6. 质量检查
            quality_issues = []

            if result["topics_count"] == 0:
                quality_issues.append("主题数为0")
            if result["resources_count"] == 0:
                quality_issues.append("资源数为0")
            if not result["has_learning_path"]:
                quality_issues.append("缺少学习路径")
            if result["practice_tasks_count"] == 0:
                quality_issues.append("练习任务数为0")
            if empty_fields:
                quality_issues.append(f"存在{len(empty_fields)}个关键空字段")

            if quality_issues:
                print(f"\n[WARN] 质量问题:")
                for issue in quality_issues:
                    print(f"  - {issue}")
                result["error"] = "; ".join(quality_issues)
            else:
                result["success"] = True
                print(f"\n[OK] 质量检查通过")

        except Exception as e:
            result["error"] = str(e)
            print(f"\n[ERROR] 测试异常: {str(e)}")

        return result

    def _check_empty_fields(self, result_data: Dict) -> List[str]:
        """检查空字段"""
        empty_fields = []

        # 检查资源
        for i, resource in enumerate(result_data.get("resources", [])):
            if not resource.get("title"):
                empty_fields.append(f"resource[{i}].title")
            if not resource.get("url"):
                empty_fields.append(f"resource[{i}].url")
            if not resource.get("summary"):
                empty_fields.append(f"resource[{i}].summary")
            if not resource.get("reason"):
                empty_fields.append(f"resource[{i}].reason")

        # 检查主题
        for i, topic in enumerate(result_data.get("topics", [])):
            if not topic.get("normalized_topic"):
                empty_fields.append(f"topic[{i}].normalized_topic")

        # 检查学习路径
        if result_data.get("learning_path"):
            stages = result_data["learning_path"].get("stages", [])
            if not stages:
                empty_fields.append("learning_path.stages")

        # 检查练习任务
        for i, task in enumerate(result_data.get("practice_tasks", [])):
            if not task.get("task_text"):
                empty_fields.append(f"practice_task[{i}].task_text")

        return empty_fields

    def test_mark_studied(self, resource_id: int) -> bool:
        """测试标记已学习"""
        try:
            response = requests.post(
                f"{self.base_url}/api/resources/{resource_id}/mark-studied",
                json={"studied": True}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"标记已学习失败: {str(e)}")
            return False

    def test_favorite(self, resource_id: int) -> bool:
        """测试收藏资源"""
        try:
            response = requests.post(
                f"{self.base_url}/api/resources/{resource_id}/favorite",
                json={"favorite": True}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"收藏资源失败: {str(e)}")
            return False

    def run_regression_tests(self):
        """运行回归测试"""
        test_cases = [
            {
                "name": "测试1: Redis缓存相关",
                "input": "Redis 缓存穿透、缓存击穿、缓存雪崩、布隆过滤器、分布式锁"
            },
            {
                "name": "测试2: Spring事务",
                "input": "Spring 事务传播机制 REQUIRED、REQUIRES_NEW、NESTED"
            },
            {
                "name": "测试3: MySQL优化",
                "input": "MySQL 索引失效、最左前缀、Explain、慢 SQL 优化"
            },
            {
                "name": "测试4: Docker",
                "input": "Docker 镜像构建、Dockerfile 优化、容器网络、docker-compose"
            },
            {
                "name": "测试5: 后端基础",
                "input": "后端缓存、数据库和框架源码都不太懂"
            }
        ]

        print("\n" + "="*60)
        print("开始回归测试")
        print("="*60)

        for test_case in test_cases:
            result = self.test_create_recommendation(
                test_case["input"],
                test_case["name"]
            )
            self.test_results.append(result)

            # 如果有资源，测试标记和收藏功能
            if result.get("task_id") and result.get("resources_count", 0) > 0:
                # 假设第一个资源ID
                resource_id = result["task_id"] * 10 + 1  # 简化假设
                print(f"\n测试资源操作 (resource_id={resource_id}):")
                mark_result = self.test_mark_studied(resource_id)
                print(f"  标记已学习: {'[OK]' if mark_result else '[FAIL]'}")
                fav_result = self.test_favorite(resource_id)
                print(f"  收藏资源: {'[OK]' if fav_result else '[FAIL]'}")

            time.sleep(2)  # 避免请求过快

    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("\n" + "="*60)
        report.append("测试报告")
        report.append("="*60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])

        report.append(f"\n总测试数: {total_tests}")
        report.append(f"通过: {passed_tests}")
        report.append(f"失败: {total_tests - passed_tests}")
        report.append(f"通过率: {passed_tests/total_tests*100:.1f}%")

        report.append(f"\n{'='*60}")
        report.append("详细结果")
        report.append(f"{'='*60}\n")

        for i, result in enumerate(self.test_results, 1):
            status = "[PASS]" if result["success"] else "[FAIL]"
            report.append(f"{i}. {result['test_name']} - {status}")
            report.append(f"   输入: {result['user_input'][:50]}...")
            report.append(f"   任务ID: {result['task_id']}")
            report.append(f"   总耗时: {result['total_duration']:.2f}s")
            report.append(f"   主题数: {result['topics_count']}")
            report.append(f"   资源数: {result['resources_count']}")
            report.append(f"   练习任务数: {result['practice_tasks_count']}")
            report.append(f"   学习路径: {'有' if result['has_learning_path'] else '无'}")

            if result["empty_fields"]:
                report.append(f"   空字段: {len(result['empty_fields'])}个")
            else:
                report.append(f"   空字段: 无")

            if result["error"]:
                report.append(f"   错误: {result['error']}")

            report.append("")

        return "\n".join(report)


if __name__ == "__main__":
    runner = E2ETestRunner()
    runner.run_regression_tests()
    report = runner.generate_report()
    print(report)

    # 保存报告
    with open("test_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n报告已保存到 test_report.txt")
