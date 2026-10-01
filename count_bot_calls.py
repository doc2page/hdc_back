# -*- coding: utf-8 -*-
"""
统计 Telegram 导出 result.json 中五个 bot 被呼唤的次数。
口径：
  - 按消息去重：一条消息里同一 bot 出现 N 次算 1 次；不同 bot 各算各的
  - 排除发送者本身就是这五个 bot 的消息（bot 自报家门不算"呼唤"）
  - 对消息全文做正则匹配（覆盖纯文本/mention 实体/bot_command 三种形态）
  - text_entities 交叉验证，口径差异打印出来
输出：bot_stats.json
"""
import json
import re
import sys
from collections import defaultdict

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
    """发送者是否为五个 bot 之一（from / actor 均检查）。"""
    for key in ("from", "actor"):
        name = msg.get(key, "")
        if isinstance(name, str):
            m = PATTERN.search(name)
            if m:
                return True
    return False


def main():
    with open("result.json", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])

    per_bot = {b: 0 for b in BOTS}
    per_bot_by_year = {b: defaultdict(int) for b in BOTS}
    callers = set()          # 呼唤过 bot 的用户（from_id）
    caller_names = {}        # from_id -> display name
    per_caller = defaultdict(int)   # from_id -> 呼唤消息数
    first, last = None, None
    first_msg, last_msg = None, None
    excluded_bot_msgs = 0
    matched_msg_count = 0    # 至少呼唤过一次的消息总数

    # 交叉验证：entity 口径
    entity_total = {b: 0 for b in BOTS}

    for msg in messages:
        if msg.get("type") != "message":
            continue
        text = full_text(msg)
        hits = set(m.group(1) for m in PATTERN.finditer(text))
        if not hits:
            continue

        # entity 口径（仅验证用，不去重）
        for ent in msg.get("text_entities", []):
            for m in PATTERN.finditer(ent.get("text", "")):
                entity_total[m.group(1)] += 1

        if sender_is_bot(msg):
            excluded_bot_msgs += 1
            continue

        matched_msg_count += 1
        for b in hits:
            per_bot[b] += 1
            year = msg.get("date", "")[:4]
            per_bot_by_year[b][year] += 1

        fid = msg.get("from_id") or msg.get("from") or "unknown"
        callers.add(fid)
        if msg.get("from"):
            caller_names[fid] = msg["from"]
        per_caller[fid] += 1

        d = msg.get("date", "")
        if d and (first is None or d < first):
            first = d
            first_msg = msg
        if d and (last is None or d > last):
            last = d
            last_msg = msg

    years = sorted({y for by in per_bot_by_year.values() for y in by})

    top_callers = [
        {
            "name": caller_names.get(fid, fid),
            "calls": cnt,
        }
        for fid, cnt in sorted(per_caller.items(), key=lambda x: -x[1])[:10]
    ]

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
        "top_callers": top_callers,
        "time_span": {
            "first_call": first,
            "last_call": last,
            "days": (
                None
                if not first or not last
                else __import__("datetime").date.fromisoformat(
                    last[:10]
                ).__sub__(
                    __import__("datetime").date.fromisoformat(first[:10])
                ).days
            ),
        },
        "first_call_text": full_text(first_msg)[:200] if first_msg else None,
        "last_call_text": full_text(last_msg)[:200] if last_msg else None,
        "meta": {
            "excluded_bot_self_messages": excluded_bot_msgs,
            "entity_cross_check_total": {b: entity_total[b] for b in BOTS},
        },
    }

    with open("bot_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"群组：{stats['group_name']}（导出共 {len(messages)} 条消息）")
    print(f"总呼唤次数：{stats['total_bot_calls']}（{matched_msg_count} 条消息，{len(callers)} 人参与）")
    for b in BOTS:
        print(f"  @{b}: {per_bot[b]}")
    print(f"时间跨度：{first} → {last}（{stats['time_span']['days']} 天）")
    print(f"排除 bot 自身消息：{excluded_bot_msgs} 条")
    # 交叉验证：entity 口径按消息去重后应与全文口径一致；偏大说明有非实体文本提及
    print("entity 口径（未去重，供对照）:", entity_total)
    print("Top 呼唤者:", [(t['name'], t['calls']) for t in top_callers[:5]])


if __name__ == "__main__":
    main()
