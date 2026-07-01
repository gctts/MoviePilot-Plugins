# MoviePilot-Plugins

自定义短剧刮削插件仓库，插件 ID 为 `ShortPlayMonitorCustom`。

改动：

- 禁用 TMDB 识别/刮削执行路径。
- 移除 AGSV、ilolicon 封面站点。
- 使用 MoviePilot 站点管理中已配置 Cookie 的 `pterclub.net`、`zmpt.cc` 检索封面。
- 站点封面 XPath：`//*[@id='kdescr']/img[1]/@src`。
- 站点检索失败时回退为视频截图。

MoviePilot 插件市场仓库地址使用本仓库 GitHub URL。

如果市场里同时维护了原版 `thsrite/MoviePilot-Plugins`，本插件会作为“短剧刮削自定义版”单独显示，不再和原版 `ShortPlayMonitor` 冲突。
