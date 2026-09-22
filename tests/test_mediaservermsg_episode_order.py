"""隔离执行插件原方法，验证季集展示；无需安装 MoviePilot 或访问外部服务。"""

import ast
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import List
from unittest.mock import Mock


PLUGIN_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins.v3/mediaservermsg/__init__.py"
)
PLUGIN_SOURCE = PLUGIN_PATH.read_text(encoding="utf-8")


def _load_plugin_class():
    method_names = {"_send_aggregated_message_impl", "_merge_continuous_episodes"}
    module = ast.parse(PLUGIN_SOURCE, filename=str(PLUGIN_PATH))
    methods = [
        node
        for cls in module.body
        if isinstance(cls, ast.ClassDef)
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name in method_names
    ]
    if {method.name for method in methods} != method_names:
        raise AssertionError("找不到待验证的插件方法")
    namespace = {
        "List": List,
        "WebhookEventInfo": SimpleNamespace,
        "MediaSource": SimpleNamespace(TMDB="tmdb"),
        "MediaType": SimpleNamespace(TV="tv"),
        "NotificationType": SimpleNamespace(MediaServer="media-server"),
        "logger": Mock(),
        "time": time,
    }
    exec(
        compile(ast.Module(body=methods, type_ignores=[]), str(PLUGIN_PATH), "exec"),
        namespace,
    )
    return type("PluginUnderTest", (), {name: namespace[name] for name in method_names})


def _event(season=None, episode=None, name=""):
    return SimpleNamespace(
        season_id=season,
        episode_id=episode,
        item_name=name,
        event="library.new",
        item_type="TV",
        overview="",
        json_object={},
    )


class EpisodeOrderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin_class = _load_plugin_class()

    def setUp(self):
        self.plugin = self.plugin_class()
        self.plugin._lifecycle_condition = threading.Condition()
        self.plugin._pending_messages = {}
        self.plugin._resolve_event_media_identity = Mock(return_value=(None, None))
        self.plugin._get_tmdb_info = Mock()
        self.plugin._get_event_action = Mock(return_value="新入库")
        self.plugin._webhook_images = {}
        self.plugin._add_play_link = False
        self.plugin.post_message = Mock()

    def _sent_episode_line(self, events):
        self.plugin.post_message.reset_mock()
        self.plugin._pending_messages["series"] = events
        self.plugin._send_aggregated_message_impl("series")
        self.plugin.post_message.assert_called_once()
        text = self.plugin.post_message.call_args.kwargs["text"]
        return next((line for line in text.splitlines() if line.startswith("📺 季集：")), None)

    def test_fallback_sorts_screenshot_order(self):
        events = [_event(1, episode) for episode in [2, 4, 1, 5, 3, 6]]
        self.assertEqual(
            self._sent_episode_line(events),
            "📺 季集：S01E01, S01E02, S01E03, S01E04, S01E05, S01E06",
        )
        self.plugin._get_tmdb_info.assert_not_called()

    def test_fallback_sorts_seasons_and_episodes_numerically(self):
        events = [_event(s, e) for s, e in [("10", "1"), (2, "10"), (1, "100"), (2, 2), (1, 99)]]
        self.assertEqual(
            self._sent_episode_line(events),
            "📺 季集：S01E99, S01E100, S02E02, S02E10, S10E01",
        )

    def test_fallback_deduplicates_normalized_season_episode_pairs(self):
        self.assertEqual(
            self._sent_episode_line([_event(1, 2), _event("01", "02"), _event(2, 2)]),
            "📺 季集：S01E02, S02E02",
        )

    def test_fallback_single_episode_and_special(self):
        for season, episode, expected in [(1, 3, "S01E03"), (0, 0, "S00E00")]:
            with self.subTest(season=season, episode=episode):
                self.assertEqual(
                    self._sent_episode_line([_event(season, episode, "原集名称")]),
                    f"📺 季集：{expected}",
                )

    def test_fallback_skips_missing_and_invalid_numbers(self):
        missing_attribute = _event(1, 4)
        del missing_attribute.season_id
        invalid = [missing_attribute, _event(None, 1), _event(1, None), _event("bad", 1), _event(1, "bad")]
        self.assertEqual(self._sent_episode_line(invalid + [_event(1, 3)]), "📺 季集：S01E03")
        self.assertIsNone(self._sent_episode_line(invalid))

    def test_merge_sorts_screenshot_order(self):
        self.assertEqual(
            self.plugin._merge_continuous_episodes([_event(1, n) for n in [2, 4, 1, 5, 3, 6]]),
            "S01E01-E06",
        )

    def test_merge_duplicate_does_not_split_continuous_range(self):
        self.assertEqual(
            self.plugin._merge_continuous_episodes([_event(1, n) for n in [2, 1, "02", 3, 3]]),
            "S01E01-E03",
        )

    def test_merge_sorts_multiple_seasons_and_three_digit_episodes(self):
        events = [_event(s, e, f"第{e}集") for s, e in [(10, 1), (2, 10), (1, 100), (2, 2), (1, 99)]]
        self.assertEqual(
            self.plugin._merge_continuous_episodes(events),
            "S01E99-E100, S02E02 第2集, S02E10 第10集, S10E01 第1集",
        )

    def test_merge_preserves_single_episode_name_and_special(self):
        for season, episode, expected in [(1, 3, "S01E03 原集名称"), (0, 0, "S00E00 原集名称")]:
            with self.subTest(season=season, episode=episode):
                self.assertEqual(
                    self.plugin._merge_continuous_episodes([_event(season, episode, "原集名称")]),
                    expected,
                )

    def test_merge_skips_missing_and_invalid_numbers(self):
        missing_attribute = _event(1, 4)
        del missing_attribute.episode_id
        invalid = [missing_attribute, _event(None, 1), _event(1, None), _event("bad", 1), _event(1, "bad")]
        self.assertEqual(
            self.plugin._merge_continuous_episodes(invalid + [_event(1, 3, "有效集")]),
            "S01E03 有效集",
        )
        self.assertEqual(self.plugin._merge_continuous_episodes(invalid), "")
        self.assertEqual(self.plugin._merge_continuous_episodes([]), "")

    def test_merge_survives_tmdb_lookup_failure(self):
        self.plugin._resolve_event_media_identity.return_value = ("tmdb", "123")
        self.plugin._get_tmdb_info.side_effect = RuntimeError("模拟 TMDB 不可用")
        self.assertEqual(
            self.plugin._merge_continuous_episodes([_event(1, n) for n in [3, 1, 2]]),
            "S01E01-E03",
        )
        self.plugin._get_tmdb_info.assert_called_once()


if __name__ == "__main__":
    unittest.main()
