#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S姐穿搭文机械自查。用法: python3 check.py 文章.md [图片总张数]

只查能被机械验证的项。人工项(意境、逐句认亲、图文关系)仍需自己过一遍。
退出码 0 = 全过, 1 = 有 FAIL。
"""
import re
import sys
from collections import Counter

FATAL = []
WARN = []


def fail(msg):
    FATAL.append(msg)


def warn(msg):
    WARN.append(msg)


def load(path):
    return open(path, encoding="utf-8").read()


def strip_marks(text):
    """去掉图片标记、主标题、空白，用于字数统计"""
    t = re.sub(r"【图\d+】", "", text)
    t = "\n".join(l for l in t.split("\n") if not l.startswith("# "))
    return re.sub(r"\s", "", t)


def paragraphs(text):
    """正文段落，不含标题与图片标记行"""
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("【图"):
            continue
        out.append(s)
    return out


def check_images(text, expected):
    marks = re.findall(r"【图(\d+)】", text)
    nums = [int(n) for n in marks]
    if expected:
        missing = [i for i in range(1, expected + 1) if i not in nums]
        if missing:
            fail(f"缺图: {missing}")
        extra = [n for n in nums if n > expected]
        if extra:
            fail(f"图号超出范围: {extra}")
    dup = [n for n, c in Counter(nums).items() if c > 1]
    if dup:
        fail(f"图号重复: {dup}")
    # 必须独占一行
    for line in text.split("\n"):
        s = line.strip()
        if "【图" in s and not re.fullmatch(r"【图\d+】", s):
            fail(f"【图XX】未独占一行: {s[:30]}")
    # 开篇不得有图
    body = text.split("\n## ")[0]
    if "【图" in body:
        fail("开篇部分出现了图片标记，开篇必须纯文字")
    print(f"  图片: {len(nums)} 张")


def check_length(text):
    """不查字数。长度由题材与密度决定，连报数都不报，免得写作时被数字牵着走。"""
    return


def check_para_variance(text):
    paras = paragraphs(text)
    lens = [len(re.sub(r"\s", "", p)) for p in paras]
    if not lens:
        fail("没有解析到正文段落")
        return
    # 不设落差数值门槛。段落参差靠内容本身的差异长出来，不靠事后数字卡。
    print(f"  段落: {len(lens)} 段")


def check_openers(text):
    """相邻段落起手词不得重复"""
    paras = paragraphs(text)
    heads = [p[:3] for p in paras]
    for i in range(1, len(heads)):
        if heads[i] == heads[i - 1]:
            fail(f"相邻段落起手词重复「{heads[i]}」: 第 {i} 段与第 {i+1} 段")
    dup = [h for h, c in Counter(heads).items() if c >= 3]
    if dup:
        warn(f"起手词全篇出现 3 次以上: {dup}（同一个开口反复用，换个说法）")


BANNED = {
    "破折号——": r"——",
    "全角冒号：": r"：",
    "半角冒号:": r"(?<![0-9a-zA-Z/])\:(?![0-9])",
    "副词地": r"[的地]{0}(?:轻轻|慢慢|静静|悄悄|安安静静|自自在在|松松|好好|巧妙)地",
    "不是A而是B对偶": r"不是[^，。]{2,20}[，]?而是",
    "论文腔": r"首先|其次|最后来说|总而言之|综上|由此可见|值得注意的是",
    "论证腔": r"同理|照样成立|一视同仁|反之，",
    "文言残留": r"两相宜|皆宜|亦可(?!以)",
    "冒号标签": r"划重点|先交个底",
    "取景框视角": r"图中|这张图|照片里|画面中|如图所示|可以看到图",
    "左右拆解": r"左边.{0,12}右边|左上.{0,12}右下",
    "营销腔": r"赋能|助力|打造专属|一站式",
}


def check_banned(text):
    body = strip_marks(text)
    for name, pat in BANNED.items():
        hits = re.findall(pat, body)
        if hits:
            fail(f"禁用项「{name}」出现 {len(hits)} 次: {hits[:3]}")


LIMITS = [
    ("S姐自称", r"S姐", 2, 3),
    ("刚好/正好家族", r"刚好|正好|刚刚好", 0, 2),
    ("快板一+动词", r"一[挎踩戴挂拎系压提收垂撞折]，", 0, 2),
]


def check_limits(text):
    body = strip_marks(text)
    for name, pat, lo, hi in LIMITS:
        n = len(re.findall(pat, body))
        if n < lo:
            fail(f"{name} 仅 {n} 处，下限 {lo}")
        elif n > hi:
            fail(f"{name} 达 {n} 处，上限 {hi}")
        else:
            print(f"  {name}: {n}")


# 配料只作参考计数，一律不判 FAIL。
# 原则：上限保留（拦"过了"），下限放松（不逼"凑够"）。
# 逼着凑够下限，写出来的每篇都含同样的配料，反而成了新的固定结构。
FLAVOR = [
    ("设问反问", r"呢[，。？]|吗？|怎么选？|什么是"),
    ("语气词", r"呢|吧|哦|~"),
    ("人群称谓", r"姐妹|集美|星人|美眉"),
    ("柔化建议词", r"不妨|不如|试试|可以大胆"),
    ("效果动词", r"显瘦|显高|显白|显腿长|减龄|遮肉|提亮|显高挑"),
    ("量词具象", r"(?:\d+|[一二三四五六七八九十两半几])+\s*(?:厘米|公分|cm|CM|度|条|水|年|码|指)|⭐"),
]


def check_flavor(text):
    """报数供参考，大致有就行。全项为 0 才提醒一句，说明整篇没有S姐的语气。"""
    body = strip_marks(text)
    counts = {name: len(re.findall(pat, body)) for name, pat in FLAVOR}
    print("  配料(参考): " + "  ".join(f"{k} {v}" for k, v in counts.items()))
    if sum(counts.values()) == 0:
        warn("六项配料一处都没有，通篇可能不是S姐在说话，回去读一遍范文")


def check_headings(text):
    for line in text.split("\n"):
        if line.startswith("## "):
            h = line[3:].strip()
            if re.match(r"^\d|^0\d|^[一二三四五六]、", h):
                fail(f"小标题带序号: {h}")
            if "，" in h or "!" in h or "！" in h:
                fail(f"小标题带效果承诺尾巴: {h}")


SIGNATURE_OPENERS = [
    "可能有人要问", "跟", "颜色上", "若是", "换成", "除了",
    "或者", "要不就是", "另外", "只是这种", "比起", "同样",
]


def check_cross_article(text, prev_path):
    """跟上一篇成稿比对起手词，防止篇与篇之间撞模板。"""
    try:
        prev = load(prev_path)
    except OSError:
        warn(f"未找到上一篇 {prev_path}，跨篇查重已跳过")
        return

    def sigs(t):
        out = set()
        for p in paragraphs(t):
            for s in SIGNATURE_OPENERS:
                if p.startswith(s):
                    out.add(s)
        return out

    dup = sigs(text) & sigs(prev)
    if dup:
        fail(
            f"与上一篇撞起手词 {sorted(dup)}（共 {len(dup)} 个）。"
            f"这些是标志性起手，连着两篇用同一个，整个号会像同一台机器印的"
        )
    else:
        print("  跨篇起手词: 与上一篇零重复")


def check_ending(text):
    ps = paragraphs(text)
    if not ps:
        return
    last = re.sub(r"\s", "", ps[-1])
    print(f"  结尾段: {len(last)} 字")
    if len(last) > 90:
        fail(f"结尾段 {len(last)} 字，超过范文最长的 89 字，宁短不长")
    # 倒数第二段若也在收尾（不含具体单品、只讲道理），提示可能写成了两段式
    if len(ps) >= 2:
        second = re.sub(r"\s", "", ps[-2])
        if len(second) < 60 and not re.search(r"配|穿|搭|件|条|双|色", second):
            warn("倒数第二段像是在收尾，检查是否写成了「升华段+号召段」两段式")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    expected = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    prev_path = sys.argv[3] if len(sys.argv) > 3 else None
    text = load(path)

    print(f"\n检查 {path}")
    print("-" * 46)
    check_images(text, expected)
    check_length(text)
    check_para_variance(text)
    check_openers(text)
    check_limits(text)
    check_flavor(text)
    check_banned(text)
    check_headings(text)
    check_ending(text)
    if prev_path:
        check_cross_article(text, prev_path)
    else:
        warn("未传上一篇路径，跨篇起手词查重未执行（用法：check.py 本篇.md 图数 上一篇.md）")

    print("-" * 46)
    for w in WARN:
        print(f"  WARN  {w}")
    for f_ in FATAL:
        print(f"  FAIL  {f_}")
    if FATAL:
        print(f"\n不通过，{len(FATAL)} 项待修。\n")
        sys.exit(1)
    print("\n机械项全过。仍需人工过：开篇意境、逐句认亲、图文关系、段尾是否落道理。\n")


if __name__ == "__main__":
    main()
