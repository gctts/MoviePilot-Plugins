"""V3 媒体库服务器通知插件的电视剧入库去重测试。"""

from types import SimpleNamespace

from app.plugins.mediaservermsg import MediaServerMsg


def _episode_event(episode: int, *, raw_item_id: str | None = None):
    """构造与 MoviePilot Emby 解析结果一致的单集事件。"""
    return SimpleNamespace(
        item_id="series-1",
        item_type="TV",
        season_id=1,
        episode_id=episode,
        json_object={
            "Item": {
                "Id": raw_item_id,
                "SeriesId": "series-1",
                "ParentIndexNumber": 1,
                "IndexNumber": episode,
            }
        },
    )


def test_episode_library_events_use_unique_raw_item_ids_for_dedupe():
    """同一电视剧的26集入库事件必须生成26个不同的去重标识。"""
    dedupe_ids = {
        MediaServerMsg._get_dedupe_item_id(
            _episode_event(episode, raw_item_id=f"episode-{episode}"),
            "library.new",
        )
        for episode in range(1, 27)
    }

    assert len(dedupe_ids) == 26
    assert "episode-1" in dedupe_ids
    assert "episode-26" in dedupe_ids


def test_episode_library_events_fall_back_to_season_and_episode():
    """缺少原始 Item.Id 时，不同集仍不能退化为相同 SeriesId。"""
    first = MediaServerMsg._get_dedupe_item_id(
        _episode_event(1),
        "library.new",
    )
    second = MediaServerMsg._get_dedupe_item_id(
        _episode_event(2),
        "library.new",
    )

    assert first == "series-1-S1-E1"
    assert second == "series-1-S1-E2"
    assert first != second


def test_duplicate_delivery_of_same_episode_keeps_same_dedupe_id():
    """同一集被媒体服务器重复投递时仍应命中去重。"""
    event = _episode_event(8, raw_item_id="episode-8")

    assert MediaServerMsg._get_dedupe_item_id(event, "library.new") == \
        MediaServerMsg._get_dedupe_item_id(event, "library.new")


def test_non_library_event_preserves_existing_series_level_dedupe():
    """播放等非入库事件继续保持现有 item_id 去重语义。"""
    event = _episode_event(3, raw_item_id="episode-3")

    assert MediaServerMsg._get_dedupe_item_id(event, "playback.start") == "series-1"
