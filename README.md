# 守夜人名册 · HDChina 回归纪念

> 站点沉睡的一千零三十七个夜晚，有人一直在敲门。

HDChina Official Group（Telegram）自 2023-11-29 至 2026-10-01 的完整聊天导出中，
2,854 位群友向 7 个 HDChina 系 bot 发出了 **14,829 次呼唤**。
站点回归之际，把这份记录做成了一张纪念证书。

## 在线版本

| 版本 | 地址 | 风格 |
|---|---|---|
| **v2（当前）** | <https://doc2page.github.io/hdc_back/> | 守夜人名册——棉纸铅字、朱砂印、限量编号证书 |
| v1（初版） | <https://doc2page.github.io/hdc_back/index_v1.html> | 午夜蓝星空调频——徽章、流星、数据卡 |

## 数据一览

- **14,829** 次呼唤 · **2,854** 位守夜人 · **1,037** 个昼夜
- 1,038 天中 **1,009 天**有人呼唤（**97.2%**，几乎没有一夜沉默）
- 最长连续守夜 **489 天**
- **198 人**全程守候（2023 年入册，2026 年仍在呼唤）
- 呼唤榜：`@hdchina_mit_bot` 7,559 · `@hdchina_group_bot` 6,487 · `@hdchina_op_bot` 428 · `@hdchina_group_mit` 298 · `@hdchina_mice_bot` 38 · `@hdwing_group_bot` 18 · `@hdchina_mushroom_bot` 1
- 第一声：`/verify@hdchina_group_bot`（2023-11-29 07:21）
- 附记：2023-12-01，Rogers 曾呼唤过一次 `/rebirth`——两年十个月后，它应验了

## 统计口径

- 七个 HDChina 系 bot（`mit_gpt_bot`、`sb_bot`、`lemonhd_mit_bot` 等非 HDChina/HDWing 系不计）
- 按消息去重：一条消息中同一 bot 出现多次算 1 次
- 排除 bot 自身发送的消息；对消息全文正则匹配（覆盖纯文本 / mention 实体 / bot_command 三种形态）
- 导出文件仅含 2023-11-28 之后消息（id 194,808 起）；283 条不带 `@bot` 后缀的命令因目标不明未计入

## 文件结构

```
result.json                 # Telegram 群聊完整导出（21,648 条消息，勿外传）
count_bot_calls.py          # 统计脚本 → bot_stats.json
bot_stats.json              # 全量统计（含每日热力、198 人名录）
bot_memorial.template.html  # v2 页面模板（__STATS__ 占位，数据与设计分离）
build_page.py               # 注入数据 → bot_memorial.html
bot_memorial.html           # v2 纪念页（成品）
index_v1.html               # v1 纪念页
bot_memorial.png            # v2 长图（2560×12196）
```

## 重建流程

```bash
python count_bot_calls.py   # 重跑统计（改 bot 名单/口径后）
python build_page.py        # 重新注入生成 bot_memorial.html
```

导出长图（Playwright，2× 高清、动画定格）：

```bash
python - <<'EOF'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width':1280,'height':900}, device_scale_factor=2)
    pg.goto('bot_memorial.html 的 file:// 绝对路径')
    pg.wait_for_timeout(3000)
    pg.evaluate('''() => {
      document.querySelectorAll(".reveal,.rollbook,.registry").forEach(el=>el.classList.add("on"));
      document.querySelectorAll("[data-count]").forEach(el=>el.textContent=(+el.dataset.count).toLocaleString("en-US"));
      document.querySelector("#stamp").classList.add("on");
    }''')
    pg.wait_for_timeout(2000)
    pg.screenshot(path='bot_memorial.png', full_page=True)
    b.close()
EOF
```

## 铭记

种子还在，就总有做种的人。
