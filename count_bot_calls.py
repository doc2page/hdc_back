# -*- coding: utf-8 -*-
"""
统计 Telegram 导出 result.json 中 HDChina 系 bot 被呼唤的次数（守夜人名册纪念数据）。
口径：
  - 七 bot（mit/group/mushroom/op/mice/hdwing/group_mit），mit_gpt_bot 已按用户要求剔除
  - 按消息去重：一条消息里同一 bot 出现 N 次算 1 次；不同 bot 各算各的
  - 排除发送者本身就是 bot 的消息
  - 对消息全文做正则匹配（覆盖纯文本/mention 实体/bot_command 三种形态）
纪念扩展：
  - daily/monthly 呼唤序列（打卡簿热力用）
  - 全程守候者名录（2023 年首呼且 2026 年仍在呼唤的人，按首呼先后入册）
  - 覆盖天数占比、最长连续守夜天数
  - 命令榜、/rebirth 彩蛋
输出：bot_stats.json
"""
import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8")

BOTS = [
    "hdchina_mit_bot",
    "hdchina_group_bot",
    "hdchina_mice_bot",
    "hdchina_mushroom_bot",
    "hdchina_op_bot",
    "hdchina_group_mit",
    "hdwing_group_bot",
]
# 长名在前防止前缀吞并；(?!\w) 防误匹配更长用户名
PATTERN = re.compile(
    "@(" + "|".join(sorted(BOTS, key=len, reverse=True)) + r")(?!\w)"
)


def full_text(msg) -> str:
    """text 字段两种形态（str / 混排数组）统一拼成完整字符串。"""
    t = msg.get("text", "")
    if isinstance(t, str):
        return t
    parts = []
    for seg in t:
        if isinstance(seg, str):
            parts.append(seg)
        else:
            parts.append(seg.get("text", ""))
    return "".join(parts)


def sender_is_bot(msg) -> bool:
    for key in ("from", "actor"):
        name = msg.get(key, "")
        if isinstance(name, str) and PATTERN.search(name):
            return True
    return False


def main():
    with open("result.json", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])

    per_bot = {b: 0 for b in BOTS}
    per_bot_by_year = {b: defaultdict(int) for b in BOTS}
    callers = set()
    caller_names = {}
    per_caller = defaultdict(int)
    first, last = None, None
    first_msg, last_msg = None, None
    excluded_bot_msgs = 0
    matched_msg_count = 0

    daily = defaultdict(int)          # yyyy-mm-dd -> 呼唤次数
    user_span = {}                    # from_id -> [first_date, last_date]
    cmd_counter = defaultdict(int)    # 命令词 -> 次数
    rebirth_easter = None

    entity_total = {b: 0 for b in BOTS}

    for msg in messages:
        if msg.get("type") != "message":
            continue
        text = full_text(msg)
        hits = set(m.group(1) for m in PATTERN.finditer(text))
        if not hits:
            continue

        for ent in msg.get("text_entities", []):
            for m in PATTERN.finditer(ent.get("text", "")):
                entity_total[m.group(1)] += 1

        if sender_is_bot(msg):
            excluded_bot_msgs += 1
            continue

        matched_msg_count += 1
        d_full = msg.get("date", "")
        d = d_full[:10]
        for b in hits:
            per_bot[b] += 1
            per_bot_by_year[b][d[:4]] += 1
        daily[d] += len(hits)

        fid = msg.get("from_id") or msg.get("from") or "unknown"
        callers.add(fid)
        if msg.get("from"):
            caller_names[fid] = msg["from"]
        per_caller[fid] += 1

        sp = user_span.setdefault(fid, [d, d])
        if d < sp[0]:
            sp[0] = d
        if d > sp[1]:
            sp[1] = d

        if d_full and (first is None or d_full < first):
            first = d_full
            first_msg = msg
        if d_full and (last is None or d_full > last):
            last = d_full
            last_msg = msg

        token = text.strip().split()
        cmd = token[0].split("@")[0] if token else ""
        if cmd.startswith("/"):
            cmd_counter[cmd] += 1
            if cmd == "/rebirth" and rebirth_easter is None:
                rebirth_easter = {
                    "date": d_full, "from": msg.get("from"), "text": text.strip()[:120]
                }

    # 时间边界与守夜统计
    d0, d1 = date.fromisoformat(first[:10]), date.fromisoformat(last[:10])
    total_days = (d1 - d0).days + 1
    covered = sum(1 for i in range(total_days)
                  if (d0 + timedelta(days=i)).isoformat() in daily)
    streak = best = 0
    for i in range(total_days):
        if (d0 + timedelta(days=i)).isoformat() in daily:
            streak += 1
            best = max(best, streak)
        else:
            streak = 0

    # 全程守候者：2023 年内首呼 且 2026 年仍在呼唤
    watchers = sorted(
        (
            {"name": caller_names.get(fid, fid), "first": sp[0]}
            for fid, sp in user_span.items()
            if sp[0] <= "2023-12-31" and sp[1] >= "2026-01-01"
        ),
        key=lambda x: (x["first"], x["name"]),
    )

    years = sorted({y for by in per_bot_by_year.values() for y in by})
    monthly = defaultdict(int)
    for d, c in daily.items():
        monthly[d[:7]] += c

    stats = {
        "group_name": data.get("name"),
        "total_messages_in_export": len(messages),
        "bots": {
            b: {
                "calls": per_bot[b],
                "by_year": {y: per_bot_by_year[b].get(y, 0) for y in years},
            }
            for b in BOTS
        },
        "total_bot_calls": sum(per_bot.values()),
        "messages_containing_call": matched_msg_count,
        "unique_callers": len(callers),
        "time_span": {
            "first_call": first,
            "last_call": last,
            "days": (d1 - d0).days,
        },
        "first_call_text": full_text(first_msg)[:200] if first_msg else None,
        "last_call_text": full_text(last_msg)[:200] if last_msg else None,
        # —— 纪念扩展 ——
        "watch": {
            "total_days": total_days,
            "covered_days": covered,
            "coverage_pct": round(covered / total_days * 100, 1),
            "longest_streak_days": best,
            "monthly": dict(sorted(monthly.items())),
            "daily": dict(sorted(daily.items())),
            "watchers_count": len(watchers),
            "watchers": watchers,
            "cmd_top": sorted(cmd_counter.items(), key=lambda x: -x[1])[:12],
            "rebirth_easter": rebirth_easter,
        },
        "top_callers": [
            {"name": caller_names.get(fid, fid), "calls": cnt}
            for fid, cnt in sorted(per_caller.items(), key=lambda x: -x[1])[:10]
        ],
        "meta": {
            "excluded_bot_self_messages": excluded_bot_msgs,
            "entity_cross_check_total": entity_total,
        },
    }

    with open("bot_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"群组：{stats['group_name']}（导出共 {len(messages)} 条消息）")
    print(f"总呼唤：{stats['total_bot_calls']} 次 · {len(callers)} 人 · {(d1-d0).days} 天")
    print(f"守夜：{total_days} 天中 {covered} 天有声（{stats['watch']['coverage_pct']}%）· 最长连续 {best} 天")
    print(f"全程守候者：{len(watchers)} 人 · /rebirth: {rebirth_easter}")
    print(f"命令榜前五：{stats['watch']['cmd_top'][:5]}")


if __name__ == "__main__":
    main()
