#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""范文语料的数据卡与按需取篇。

存在的理由：通读 16 篇全文要花约 20k token，而真正救回稿子的从来不是"读过"，
是"量过"。数字一次算清就够了，之后每次创作照数字执行即可。

    python3 corpus.py card          打印数据卡（约 1k token，替代通读）
    python3 corpus.py show 7 12     只取出第 7、12 篇原文精读（临帖用）
    python3 corpus.py list          列出 16 篇篇名，挑临帖对象用
"""
import re
import signal
import sys
from pathlib import Path

# 输出常被管到 head，管道提前关闭时不要抛 BrokenPipeError
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

CORPUS = Path(__file__).resolve().parent.parent / "references" / "sample-articles-full.md"

QUIP = r"[^,.]{1,6}一[^,.]{1,2}[,][^,.]{0,8}就"
QUALITY = (
    r"高级|知性|优雅|雅致|从容|慵懒|清爽|得体|风度|隽永|矜贵|文气|书卷|闲情|悠然|"
    r"大气|潇洒|精致|端庄|温婉|松弛|利落|干练|耐看|恰到好处|腔调|品味|气息|韵味|"
    r"浪漫|纯真|柔美|娇嫩|清新|温柔|甜美|典雅|贵气|摩登|时髦|风情|俏丽|纯净|纯粹|"
    r"淡雅|脱俗|洒脱|复古|明媚|沉静|轻盈|文雅|养眼|清透|舒服|和谐|随性|自在"
)


def norm(t):
    return t.replace("，", ",").replace("。", ".").replace("、", ",")


def articles():
    parts = re.split(r"\n## 文章(\d+)：([^\n]+)\n", CORPUS.read_text(encoding="utf-8"))
    return [(parts[i], parts[i + 1], parts[i + 2]) for i in range(1, len(parts), 3)]


def paras(body):
    """正文段落。原文各篇之间用 --- 分隔，别把分隔符算成最后一段。"""
    return [
        p.strip()
        for p in body.strip().split("\n\n")
        if p.strip() and set(p.strip()) != {"-"}
    ]


def opening(body):
    """首个小标题之前的段落。小标题在原文里是独立的极短行。"""
    ps = paras(body)
    out = []
    for p in ps:
        if len(re.sub(r"\s", "", p)) <= 8 and not p.endswith("。"):
            break
        out.append(p)
    return out or ps[:3]


def card():
    rows = []
    for num, title, body in articles():
        b = norm(re.sub(r"\s", "", body))
        k = len(b) / 1000
        op = opening(body)
        oplen = sum(len(re.sub(r"\s", "", p)) for p in op) // len(op)
        tail = re.sub(r"\s", "", paras(body)[-1])
        rows.append(
            dict(
                n=num, t=title[:16], chars=len(b), op_n=len(op), op_avg=oplen,
                quality=len(re.findall(QUALITY, b)) / k, quip=len(re.findall(QUIP, b)),
                tail=len(tail),
            )
        )

    def rng(key):
        v = [r[key] for r in rows]
        return min(v), max(v), sum(v) / len(v)

    print("# 范文数据卡（16 篇实测，替代通读全文）\n")
    print(f"{'#':>3} {'篇名':<18}{'字数':>6}{'开篇段数':>7}{'开篇字/段':>8}{'评价词/千':>9}{'机灵句':>6}{'结尾字':>6}")
    print("-" * 66)
    for r in rows:
        print(
            f"{r['n']:>3} {r['t']:<18}{r['chars']:>6}{r['op_n']:>7}{r['op_avg']:>8}"
            f"{r['quality']:>9.1f}{r['quip']:>6}{r['tail']:>6}"
        )
    print("-" * 66)
    for label, key, fmt in [
        ("全文字数", "chars", "{:.0f}"),
        ("开篇段数", "op_n", "{:.0f}"),
        ("开篇字/段", "op_avg", "{:.0f}"),
        ("评价词/千字", "quality", "{:.1f}"),
        ("结尾段字数", "tail", "{:.0f}"),
    ]:
        lo, hi, av = rng(key)
        print(f"  {label:<12} {fmt.format(lo)} ~ {fmt.format(hi)}   均值 {fmt.format(av)}")
    print(f"  {'机灵句':<12} 全库合计 {sum(r['quip'] for r in rows)} 处（这个句式她基本不用）")
    print("\n照这些数字执行即可，不必再通读全文。要临帖时用 show 单独取那一两篇。")


def show(nums):
    want = set(nums)
    for num, title, body in articles():
        if num in want:
            print(f"\n{'=' * 60}\n## 文章{num}：{title}\n{'=' * 60}{body.rstrip()}\n")


def lst():
    print("16 篇篇名（挑临帖对象用，取篇用 corpus.py show N）\n")
    for num, title, body in articles():
        print(f"  {num:>3}  {title}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "card"
    if cmd == "card":
        card()
    elif cmd == "show":
        show(sys.argv[2:])
    elif cmd == "list":
        lst()
    else:
        print(__doc__)
