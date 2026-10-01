# -*- coding: utf-8 -*-
"""
构建：读 bot_stats.json，注入 bot_memorial.template.html 的 __STATS__ 占位，
输出 bot_memorial.html。数据与设计分离——改口径重跑统计后只需重跑本脚本。
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open("bot_stats.json", encoding="utf-8") as f:
    stats = json.load(f)

with open("bot_memorial.template.html", encoding="utf-8") as f:
    tpl = f.read()

# 只注入页面实际用到的字段，daily 全量（热力图需要）
payload = {
    "watch": {
        "daily": stats["watch"]["daily"],
        "monthly": stats["watch"]["monthly"],
        "watchers": stats["watch"]["watchers"],
    },
    "top_callers": stats["top_callers"],
}

html = tpl.replace("__STATS__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

with open("bot_memorial.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"bot_memorial.html 构建完成（{len(html) // 1024} KB，注入 {len(payload['watch']['daily'])} 日热力 + {len(payload['watch']['watchers'])} 位守夜人）")
