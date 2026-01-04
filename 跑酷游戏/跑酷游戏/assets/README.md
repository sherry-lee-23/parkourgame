# 资源目录说明

为方便管理角色、敌人和特效资源，新增了以下目录结构：

- `assets/player/`：玩家相关贴图（站立/跑动/跳跃等帧）。
- `assets/enemy/`：敌人贴图（slime、goblin、bat、boss 等），当前缺少：
  - `assets/enemy/slime.png`
  - `assets/enemy/goblin.png`
  - `assets/enemy/bat.png`
  - `assets/enemy/boss.png`
- `assets/effects/`：攻击、命中特效或弹道图片，当前暂无素材，可在此添加 `hit.png`、`bullet.png` 等。

代码会优先从这些目录加载资源，缺失时使用颜色方块占位，方便后续替换为正式美术资源。
