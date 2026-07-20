"""
xhs_crawler.py — 小红书账号采集工具

⚠️ 优先使用 opencli（推荐）:
   opencli xiaohongshu user USER_ID -f yaml
   opencli xiaohongshu search "关键词" -f yaml
   opencli xiaohongshu note "NOTE_URL" -f yaml

本 Playwright 方案仅在需要以下场景时使用备用：
- 需要解析已登录个人主页的详细历史笔记列表
- opencli 无法获取到足够的历史笔记数据
- 需要采集笔记中的图片资源

使用方式:
    from tools.xhs_crawler import XHSCrawler
    crawler = XHSCrawler()
    notes = await crawler.get_recent_notes("用户主页URL", max_notes=30)
"""

import json
import re
import asyncio
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict


# ============================================================
# 数据模型
# ============================================================

@dataclass
class UserInfo:
    nickname: str = ""
    followers: int = 0
    likes: int = 0
    notes_count: int = 0


@dataclass
class NoteInfo:
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


# ============================================================
# 采集器（备用方案，首选 opencli）
# ============================================================

class XHSCrawler:
    """小红书笔记采集器（备用方案）"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.page = None

    async def _init_browser(self):
        """初始化浏览器（使用已有登录状态）"""
        from playwright.async_api import async_playwright

        p = await async_playwright().start()
        self.browser = await p.chromium.launch(
            headless=self.headless,
        )
        self.page = await self.browser.new_page(
            viewport={"width": 390, "height": 844},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            )
        )

    async def _scroll_load(self, max_notes: int = 30) -> list:
        """自动滚动加载笔记列表"""
        notes_data = []
        last_count = 0
        retry_count = 0

        while len(notes_data) < max_notes and retry_count < 5:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            current_notes = await self._parse_note_list()

            if len(current_notes) > last_count:
                last_count = len(current_notes)
                notes_data = current_notes
                retry_count = 0
            else:
                retry_count += 1

        return notes_data[:max_notes]

    async def _parse_note_list(self) -> list:
        """解析笔记列表页"""
        notes = []

        try:
            note_elements = await self.page.query_selector_all(
                "section.note-item, .note-item, [class*=note], .feeds-page .note-item"
            )

            for el in note_elements:
                note = NoteInfo()
                try:
                    title_el = await el.query_selector(".title, h3, [class*=title]")
                    if title_el:
                        note.title = await title_el.inner_text()

                    like_el = await el.query_selector(".like-wrapper .count, [class*=like]")
                    if like_el:
                        note.likes = self._parse_count(await like_el.inner_text())

                    link_el = await el.query_selector("a")
                    if link_el:
                        href = await link_el.get_attribute("href")
                        if href:
                            note.note_id = self._extract_note_id(href)

                    img_el = await el.query_selector("img")
                    if img_el:
                        src = await img_el.get_attribute("src")
                        if src:
                            note.images.append(src)

                except Exception:
                    continue

                if note.title:
                    notes.append(note)

        except Exception as e:
            print(f"解析笔记列表失败: {e}")

        return notes

    async def _parse_note_detail(self, note_id: str) -> Optional[NoteInfo]:
        """进入笔记详情页解析完整数据（如 opencli 不可用时备用）"""
        try:
            await self.page.goto(
                f"https://www.xiaohongshu.com/explore/{note_id}",
                wait_until="networkidle"
            )
            await asyncio.sleep(2)

            note = NoteInfo(note_id=note_id)

            title_el = await self.page.query_selector("#detail-title, .title, h1")
            if title_el:
                note.title = await title_el.inner_text()

            content_el = await self.page.query_selector(
                ".note-content, .content, [class*=content]"
            )
            if content_el:
                note.content = await content_el.inner_text()

            like_el = await self.page.query_selector(
                ".like-wrapper .count, [class*=like] .count"
            )
            if like_el:
                note.likes = self._parse_count(await like_el.inner_text())

            collect_el = await self.page.query_selector(
                ".collect-wrapper .count, [class*=collect] .count"
            )
            if collect_el:
                note.collects = self._parse_count(await collect_el.inner_text())

            comment_el = await self.page.query_selector(
                ".comment-wrapper .count, [class*=comment] .count"
            )
            if comment_el:
                note.comments = self._parse_count(await comment_el.inner_text())

            share_el = await self.page.query_selector(
                ".share-wrapper .count, [class*=share] .count"
            )
            if share_el:
                note.shares = self._parse_count(await share_el.inner_text())

            tags = await self.page.query_selector_all(".tag, [class*=tag]")
            for tag_el in tags:
                tag_text = await tag_el.inner_text()
                note.tags.append(tag_text.strip().lstrip("#"))

            imgs = await self.page.query_selector_all(
                ".carousel img, .slide img, [class*=image] img"
            )
            for img_el in imgs:
                src = await img_el.get_attribute("src")
                if src and src not in note.images:
                    note.images.append(src)

            time_el = await self.page.query_selector("time, .date, [class*=time]")
            if time_el:
                note.publish_time = await time_el.get_attribute("datetime") or await time_el.inner_text()

            return note

        except Exception as e:
            print(f"解析笔记详情失败 {note_id}: {e}")
            return None

    async def get_user_info(self, profile_url: str) -> UserInfo:
        """获取用户主页信息"""
        if not self.page:
            await self._init_browser()

        await self.page.goto(profile_url, wait_until="networkidle")
        await asyncio.sleep(3)

        user = UserInfo()

        try:
            name_el = await self.page.query_selector(
                ".username, .user-name, [class*=nickname]"
            )
            if name_el:
                user.nickname = await name_el.inner_text()

            follower_el = await self.page.query_selector(
                ".follower .count, [class*=follower] .num, [class*=fans]"
            )
            if follower_el:
                user.followers = self._parse_count(await follower_el.inner_text())

            like_el = await self.page.query_selector(
                ".liked .count, [class*=liked] .num, [class*=like-count]"
            )
            if like_el:
                user.likes = self._parse_count(await like_el.inner_text())

            note_count_el = await self.page.query_selector(
                ".note-count, [class*=note-count], [class*=note-num]"
            )
            if note_count_el:
                user.notes_count = self._parse_count(await note_count_el.inner_text())

        except Exception as e:
            print(f"获取用户信息失败: {e}")

        return user

    async def get_recent_notes(
        self, profile_url: str, max_notes: int = 30
    ) -> list:
        """获取最近N篇笔记"""
        if not self.page:
            await self._init_browser()

        user_info = await self.get_user_info(profile_url)
        notes = await self._scroll_load(max_notes=max_notes)

        return notes

    async def save_notes_to_json(self, notes: list, filepath: str):
        """保存笔记数据到 JSON 文件"""
        data = [asdict(note) for note in notes]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(notes)} 篇笔记到 {filepath}")

    async def close(self):
        if self.browser:
            await self.browser.close()

    @staticmethod
    def _parse_count(text: str) -> int:
        text = text.strip()
        if not text:
            return 0
        if "万" in text:
            return int(float(text.replace("万", "").strip()) * 10000)
        if "亿" in text:
            return int(float(text.replace("亿", "").strip()) * 100000000)
        try:
            return int(text.replace(",", ""))
        except ValueError:
            return 0

    @staticmethod
    def _extract_note_id(url: str) -> str:
        match = re.search(r"/([a-f0-9]{24})", url)
        return match.group(1) if match else ""


async def main():
    """示例：如何使用采集器（备用方案）"""
    print("⚠️  推荐使用 opencli 采集:")
    print('   opencli xiaohongshu user USER_ID -f yaml')
    print('   opencli xiaohongshu search "美短" -f yaml')
    print()
    crawler = XHSCrawler(headless=False)
    try:
        profile_url = input("请输入小红书主页URL: ")
        notes = await crawler.get_recent_notes(profile_url, max_notes=30)
        await crawler.save_notes_to_json(notes, "memory/raw_notes.json")
        print(f"采集完成，共 {len(notes)} 篇笔记")
    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
