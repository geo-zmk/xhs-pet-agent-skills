"""
analyzer.py — 小红书笔记数据分析工具

提供内容分类、爆款评分、低表现分析等功能。

使用方式:
    from tools.analyzer import AccountAnalyzer
    analyzer = AccountAnalyzer()
    report = analyzer.full_analysis(notes)
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from collections import Counter


# ============================================================
# 数据模型
# ============================================================

@dataclass
class NoteStats:
    note_id: str = ""
    title: str = ""
    content: str = ""
    publish_time: str = ""
    likes: int = 0
    collects: int = 0
    comments: int = 0
    shares: int = 0
    images: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    category: str = ""
    hot_score: float = 0.0


@dataclass
class AnalysisReport:
    account_name: str = ""
    total_notes: int = 0
    avg_likes: float = 0.0
    avg_collects: float = 0.0
    avg_comments: float = 0.0
    category_distribution: dict = field(default_factory=dict)
    top_notes: list = field(default_factory=list)
    low_performers: list = field(default_factory=list)
    viral_patterns: dict = field(default_factory=dict)
    improvement_suggestions: list = field(default_factory=list)
    account_profile: dict = field(default_factory=dict)


# ============================================================
# 内容分类器
# ============================================================

class ContentClassifier:
    """笔记内容分类器"""

    CATEGORY_RULES = {
        "花色科普": {
            "keywords": [
                "花色", "虎斑", "银虎斑", "棕虎斑", "蓝色", "奶油色",
                "玳瑁", "文身", "花纹", "颜色", "稀有", "加白",
                "鱼骨纹", "古典纹", "斑点纹"
            ],
            "weight": 1.0
        },
        "品种鉴定": {
            "keywords": [
                "鉴定", "品相", "纯种", "血统", "CFA", "标准",
                "正规猫舍", "赛级", "宠物级", "品标", "品种标准",
                "美短vs", "美短和", "区别", "对比"
            ],
            "weight": 1.0
        },
        "成长日记": {
            "keywords": [
                "成长", "幼猫", "小时候", "长大了", "变化", "日常",
                "我家猫", "我的猫", "每天", "记录", "从..到",
                "第一天", "满月", "个月"
            ],
            "weight": 1.0
        },
        "猫咪行为": {
            "keywords": [
                "行为", "性格", "粘人", "聪明", "调皮", "乖巧",
                "拆家", "跑酷", "踩奶", "呼噜", "睡觉",
                "为什么", "一直叫", "咬人", "抓人"
            ],
            "weight": 1.0
        },
        "养猫经验": {
            "keywords": [
                "经验", "攻略", "避坑", "推荐", "平替", "好物",
                "猫粮", "猫砂", "用品", "玩具", "猫窝",
                "省钱", "新手", "必备"
            ],
            "weight": 1.0
        },
        "健康知识": {
            "keywords": [
                "健康", "生病", "医院", "疫苗", "驱虫", "绝育",
                "呕吐", "拉稀", "尿闭", "猫瘟", "HCM",
                "体检", "牙齿", "眼睛", "耳朵"
            ],
            "weight": 1.0
        }
    }

    def classify(self, note: dict) -> str:
        """对单篇笔记进行分类"""
        text = (note.get("title", "") + " " + note.get("content", "")).lower()
        tags = " ".join(note.get("tags", []))

        scores = {}
        for category, rules in self.CATEGORY_RULES.items():
            score = 0
            for keyword in rules["keywords"]:
                if keyword.lower() in text or keyword.lower() in tags:
                    score += rules["weight"]
            scores[category] = score

        if max(scores.values()) == 0:
            return "其他"

        return max(scores, key=scores.get)


# ============================================================
# 爆款评分器
# ============================================================

class HotScorer:
    """爆款评分计算器"""

    def __init__(self):
        self.weights = {
            "like_rate": 0.20,
            "collect_rate": 0.25,
            "comment_rate": 0.25,
            "interact_rate": 0.20,
            "growth_contribution": 0.10,
        }

    def calculate(self, note: dict, followers: int = 0) -> float:
        """
        计算单篇笔记的 HotScore

        公式:
        HotScore = 点赞率(20%) + 收藏率(25%) + 评论率(25%)
                  + 互动率(20%) + 涨粉贡献(10%)
        """
        likes = note.get("likes", 0) or 0
        collects = note.get("collects", 0) or 0
        comments = note.get("comments", 0) or 0
        shares = note.get("shares", 0) or 0

        # 预估曝光量（基于互动量反推）
        estimated_impression = (likes + collects * 2 + comments * 3 + shares * 4) * 10
        if estimated_impression == 0:
            estimated_impression = 1000  # 默认最小值

        # 各维度分（归一化到0-100）
        like_rate = min(likes / max(estimated_impression, 1) * 100, 30)
        collect_rate = min(collects / max(estimated_impression, 1) * 100, 40)
        comment_rate = min(comments / max(estimated_impression, 1) * 100, 40)
        interact_rate = min(
            (likes + collects * 2 + comments * 3 + shares * 4)
            / max(estimated_impression, 1) * 100,
            50
        )

        # 涨粉贡献（无数据时使用默认值）
        growth_rate = 5.0

        # 加权总分
        score = (
            like_rate * self.weights["like_rate"]
            + collect_rate * self.weights["collect_rate"]
            + comment_rate * self.weights["comment_rate"]
            + interact_rate * self.weights["interact_rate"]
            + growth_rate * self.weights["growth_contribution"]
        )

        return round(score, 2)


# ============================================================
# 分析器主类
# ============================================================

class AccountAnalyzer:
    """账号分析器"""

    def __init__(self):
        self.classifier = ContentClassifier()
        self.scorer = HotScorer()

    def full_analysis(self, notes: List[dict], followers: int = 0) -> AnalysisReport:
        """执行完整分析"""
        report = AnalysisReport()

        if not notes:
            return report

        # 基本信息
        report.total_notes = len(notes)
        report.avg_likes = sum(n.get("likes", 0) or 0 for n in notes) / len(notes)
        report.avg_collects = sum(n.get("collects", 0) or 0 for n in notes) / len(notes)
        report.avg_comments = sum(n.get("comments", 0) or 0 for n in notes) / len(notes)

        # 内容分类
        categories = []
        for note in notes:
            cat = self.classifier.classify(note)
            categories.append(cat)
            note["category"] = cat

        cat_counter = Counter(categories)
        total = len(categories)
        report.category_distribution = {
            cat: {
                "count": count,
                "percentage": round(count / total * 100, 1)
            }
            for cat, count in cat_counter.most_common()
        }

        # HotScore 计算
        scored_notes = []
        for note in notes:
            score = self.scorer.calculate(note, followers)
            scored_notes.append((score, note))

        scored_notes.sort(key=lambda x: x[0], reverse=True)

        # Top10 爆款
        report.top_notes = [
            {
                "rank": i + 1,
                "title": note.get("title", ""),
                "category": note.get("category", ""),
                "hot_score": score,
                "likes": note.get("likes", 0),
                "collects": note.get("collects", 0),
                "comments": note.get("comments", 0),
                "shares": note.get("shares", 0),
            }
            for i, (score, note) in enumerate(scored_notes[:10])
        ]

        # 低表现分析（最低5篇）
        lowest = scored_notes[-5:] if len(scored_notes) >= 5 else scored_notes
        lowest.reverse()
        report.low_performers = [
            {
                "rank": len(scored_notes) - i,
                "title": note.get("title", ""),
                "category": note.get("category", ""),
                "hot_score": score,
                "failure_reasons": self._analyze_failure(note, score)
            }
            for i, (score, note) in enumerate(lowest)
        ]

        # 爆款模式分析
        if report.top_notes:
            report.viral_patterns = self._analyze_viral_patterns(
                [n for _, n in scored_notes[:10]]
            )

        # 改进建议
        report.improvement_suggestions = self._generate_suggestions(report)

        # 账号画像
        report.account_profile = self._build_profile(report, notes)

        return report

    def _analyze_failure(self, note: dict, score: float) -> list:
        """分析低表现原因"""
        reasons = []

        title = note.get("title", "")
        likes = note.get("likes", 0) or 0
        collects = note.get("collects", 0) or 0
        comments = note.get("comments", 0) or 0

        # 标题长度检查
        if len(title) < 5:
            reasons.append("标题过短，缺乏吸引力")
        elif not any(c in title for c in ["｜", "|", "！", "？"]):
            reasons.append("标题缺少分隔符或情绪符号")

        # 互动率检查
        total_interact = likes + collects * 2 + comments * 3
        if total_interact < 100:
            reasons.append("整体互动偏低，选题不吸引目标用户")

        # 收藏率
        if collects == 0:
            reasons.append("零收藏，内容缺乏干货价值")

        # 评论率
        if comments == 0:
            reasons.append("零评论，缺少互动引导")

        if not reasons:
            reasons.append("表现平平，需要更突出的差异化内容")

        return reasons

    def _analyze_viral_patterns(self, top_notes: List[dict]) -> dict:
        """分析爆款共同模式"""
        titles = [n.get("title", "") for n in top_notes if n.get("title")]

        patterns = {
            "title_patterns": self._extract_title_patterns(titles),
            "common_categories": [
                n.get("category") for n in top_notes if n.get("category")
            ],
            "avg_title_length": round(
                sum(len(t) for t in titles) / len(titles)
            ) if titles else 0,
        }

        return patterns

    def _extract_title_patterns(self, titles: list) -> list:
        """提取标题模式"""
        patterns = []

        # 数字模式
        has_number = sum(1 for t in titles if any(c.isdigit() for c in t))
        if has_number > len(titles) * 0.5:
            patterns.append("数字（清单/对比/教程）")

        # 对比模式
        has_compare = sum(
            1 for t in titles
            if any(k in t for k in ["vs", "VS", "对比", "区别", "还是"])
        )
        if has_compare > 0:
            patterns.append("对比式（A vs B）")

        # 提问模式
        has_question = sum(
            1 for t in titles
            if any(k in t for k in ["？", "?", "怎么", "如何", "为什么"])
        )
        if has_question > 0:
            patterns.append("提问式（引发好奇心）")

        # 分隔符使用
        has_sep = sum(
            1 for t in titles
            if any(k in t for k in ["｜", "|", "·", "•"])
        )
        if has_sep > 0:
            patterns.append("分隔符结构（信息分层）")

        return patterns if patterns else ["暂无明显模式"]

    def _generate_suggestions(self, report: AnalysisReport) -> list:
        """生成优化建议"""
        suggestions = []

        # 根据类别分布给建议
        cat_dist = report.category_distribution
        if cat_dist:
            cats = list(cat_dist.keys())
            # 找出占比最低的类别
            lowest_cat = min(cat_dist, key=lambda k: cat_dist[k]["count"])
            suggestions.append(
                f"增加「{lowest_cat}」方向的内容，目前占比不足，用户有需求缺口"
            )

        # 根据爆款模式给建议
        if report.viral_patterns:
            patterns = report.viral_patterns.get("title_patterns", [])
            if patterns:
                suggestions.append(
                    f"标题继续使用{','.join(patterns[:2])}格式，表现最好"
                )

        # 通用建议
        suggestions.extend([
            "固定发布时间（建议晚8点），培养用户阅读习惯",
            "每篇末尾增加互动引导，提升评论率",
            "持续记录和分析数据，建立账号增长模型",
        ])

        return suggestions

    def _build_profile(self, report: AnalysisReport, notes: list) -> dict:
        """构建或更新账号画像"""
        return {
            "total_notes_analyzed": report.total_notes,
            "avg_hot_score": round(
                sum(n.get("hot_score", 0) for n in notes
                    if isinstance(n, dict)) / max(len(notes), 1),
                2
            ),
            "best_categories": [
                cat for cat, data in sorted(
                    report.category_distribution.items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )[:3]
            ],
            "viral_patterns": report.viral_patterns,
            "last_analysis_date": datetime.now().isoformat(),
        }

    def load_notes_from_json(self, filepath: str) -> List[dict]:
        """从 JSON 文件加载笔记"""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_report(self, report: AnalysisReport, filepath: str):
        """保存分析报告"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
        print(f"分析报告已保存到 {filepath}")


# ============================================================
# 快捷使用
# ============================================================

def main():
    import sys
    if len(sys.argv) < 2:
        print("使用方式: python analyzer.py <notes_json_path>")
        return

    notes_path = sys.argv[1]
    analyzer = AccountAnalyzer()
    notes = analyzer.load_notes_from_json(notes_path)
    report = analyzer.full_analysis(notes)

    # 输出摘要
    print(f"\n📊 分析完成 - 共 {report.total_notes} 篇笔记")
    print(f"平均点赞: {report.avg_likes:.0f}")
    print(f"平均收藏: {report.avg_collects:.0f}")
    print(f"平均评论: {report.avg_comments:.0f}")
    print(f"\n📂 内容分布:")
    for cat, data in report.category_distribution.items():
        bar = "█" * int(data["percentage"] / 5)
        print(f"  {cat}: {bar} {data['percentage']}%")

    # 保存报告
    analyzer.save_report(report, "memory/analysis_report.json")


if __name__ == "__main__":
    main()
