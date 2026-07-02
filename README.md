# MoviePilot-Plugins

自定义短剧刮削插件仓库，插件 ID 为 `ShortPlayMonitorCustom`，适配 MoviePilot V2 插件市场。

## 改动

- 禁用 TMDB 识别/刮削执行路径。
- 移除 AGSV、ilolicon 封面站点。
- 使用 MoviePilot 站点管理中已配置 Cookie 的 `pterclub.net`、`zmpt.cc` 检索封面。
- 站点检索失败时回退为视频截图。
- 支持源目录和目标目录双向删除联动。
- 整部剧目录删除时联动删除 qB 下载记录，不删除下载文件。

## 使用说明

监控方式：

- `fast`：性能模式，内部处理系统操作类型选择最优解。
- `compatibility`：兼容模式，目录同步性能降低且 NAS 不能休眠，但可以兼容挂载的远程共享目录如 SMB，建议使用。

是否重命名：

- `true` 自定义识别词。
- `false`。
- `smart` 自动取剧名。

封面比例：`2:3`
