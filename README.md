# MoviePilot ShortPlayMonitor Custom

自定义短剧刮削插件仓库。

改动：

- 禁用 TMDB 识别/刮削执行路径。
- 移除 AGSV、ilolicon 封面站点。
- 使用 MoviePilot 站点管理中已配置 Cookie 的 `pterclub.net`、`zmpt.cc` 检索封面。
- 站点封面 XPath：`//*[@id='kdescr']/img[1]/@src`。
- 站点检索失败时回退为视频截图。

MoviePilot 插件市场仓库地址使用本仓库 GitHub URL。
