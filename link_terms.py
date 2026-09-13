"""実験ログの本文に、用語集へのリンク（クリックでポップアップ）を差し込む。

手で付けていくと実験が増えるほど抜けが出るので、機械的に付ける。
ただし壊すと本文が変わってしまうので、次の2つを守る。

  1. 差し込むのはタグだけ。本文の文字は1文字も変えない
     （タグを全部剥がした結果が処理前と一致することを最後に検算する）
  2. 表・見出し・コード・既にリンク済みの場所には触らない

同じ語を何度もリンクしても読みにくいだけなので、1実験につき1語1回まで。

Usage:
    python link_terms.py            # 差し込んで保存
    python link_terms.py --dry-run  # 何件付くかだけ見る
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "site", "template.html")
GLOSSARY = os.path.join(HERE, "glossary.json")

# 本文に出てきたときにリンクしたい語。用語集に存在しない語を書くと止まる。
ALLOW = [
    "ノード", "ネットワーク", "SOP", "DOP", "POP", "ROP",
    "ジオメトリ", "ポイント", "バーテックス", "プリミティブ", "ポリゴン",
    "アトリビュート", "ディテールアトリビュート", "トポロジ", "法線",
    "バウンディングボックス", "グループ", "ボリューム", "ボクセル",
    "パックプリミティブ",
    "subdivide", "Catmull-Clark", "mountain", "ノイズ", "scatter",
    "copy to points", "for-each", "イテレーション", "wrangle", "VEX",
    "polyextrude", "boolean", "voronoi fracture",
    "シミュレーション", "ソルバ", "RBD", "Vellum", "Pyro", "FLIP",
    "サブステップ", "キャッシュ", "フラクチャ", "コンストレイント",
    "スティフネス", "ピン", "密度", "散逸", "発生源",
    "レンダリング", "Karma", "Mantra", "OpenGL ROP", "ビューポート",
    "ワイヤーフレーム", "フリップブック", "距離減衰",
    "パラメータ", "クック", "表示フラグ", "バイパス", "HDA",
    "hython", "HOM", "Apprentice",
]

# この中の文字はリンクしない。数値表や見出しに点線が入ると読みにくい。
SKIP_TAGS = {"code", "button", "table", "thead", "tbody", "tr", "th", "td",
             "h1", "h2", "h3", "h4", "figcaption", "script", "style", "a"}
SKIP_CLASSES = ("chip", "path", "label", "eyebrow", "thumb-no", "gloss-meta")
VOID_TAGS = {"br", "img", "hr", "input", "meta", "link", "source"}

MAX_PER_ARTICLE = 12


def glossary_keys():
    with io.open(GLOSSARY, encoding="utf-8") as fp:
        data = json.load(fp)
    keys = set()
    for cat in data["categories"]:
        for entry in cat["terms"]:
            keys.add(entry["term"].strip())
            for part in entry["term"].split("/"):
                if part.strip():
                    keys.add(part.strip())
    return keys


def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text)


def is_ascii_term(term):
    return all(ord(ch) < 128 for ch in term)


def link_article(body, pattern, used_globally):
    """1つの実験の中身にリンクを差し込む。used は実験ごとにリセットする。"""
    used = set()
    stack = []
    out = []
    added = 0

    for token in re.split(r"(<[^>]+>)", body):
        if not token:
            continue

        if token.startswith("<"):
            out.append(token)
            match = re.match(r"</?\s*([A-Za-z][\w-]*)", token)
            if not match:
                continue
            name = match.group(1).lower()
            if token.startswith("</"):
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i][0] == name:
                        del stack[i:]
                        break
            elif name not in VOID_TAGS and not token.endswith("/>"):
                skip = name in SKIP_TAGS or any(
                    f'class="{c}' in token or f' {c}"' in token or f' {c} ' in token
                    for c in SKIP_CLASSES
                )
                stack.append((name, skip))
            continue

        if any(skip for _, skip in stack) or added >= MAX_PER_ARTICLE:
            out.append(token)
            continue

        pos = 0
        pieces = []
        for match in pattern.finditer(token):
            term = match.group(0)
            if term in used:
                continue
            if is_ascii_term(term):
                before = token[match.start() - 1] if match.start() else ""
                after = token[match.end()] if match.end() < len(token) else ""
                if re.match(r"[A-Za-z0-9_]", before) or re.match(r"[A-Za-z0-9_]", after):
                    continue
            if match.start() < pos:
                continue
            pieces.append(token[pos:match.start()])
            pieces.append(f'<button class="term" data-term="{term}">{term}</button>')
            pos = match.end()
            used.add(term)
            used_globally.add(term)
            added += 1
            if added >= MAX_PER_ARTICLE:
                break
        pieces.append(token[pos:])
        out.append("".join(pieces))

    return "".join(out), added


def main():
    dry = "--dry-run" in sys.argv

    keys = glossary_keys()
    missing = [t for t in ALLOW if t not in keys]
    if missing:
        raise SystemExit(f"用語集に無い語が ALLOW に入っている: {missing}")

    # 長い語を先に当てる。「ワイヤーフレーム」を「フレーム」で切らないため。
    ordered = sorted(ALLOW, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(t) for t in ordered))

    with io.open(TARGET, encoding="utf-8") as fp:
        page = fp.read()
    before_text = strip_tags(page)

    parts = re.split(r'(<article class="entry[^"]*" id="exp\d+">)', page)
    result = [parts[0]]
    total = 0
    used_globally = set()

    for i in range(1, len(parts), 2):
        head, body = parts[i], parts[i + 1]
        end = body.find("</article>")
        inner, rest = (body[:end], body[end:]) if end != -1 else (body, "")

        # すでに手で付けた語は、その実験では触らない
        already = set(re.findall(r'data-term="([^"]+)"', inner))
        linked, added = link_article(
            inner,
            re.compile("|".join(re.escape(t) for t in ordered if t not in already)),
            used_globally,
        )
        total += added
        result.append(head)
        result.append(linked + rest)

    page_out = "".join(result)

    after_text = strip_tags(page_out)
    if after_text != before_text:
        raise SystemExit("本文が変わってしまった。中止する。")

    print(f"リンクを {total} 件差し込んだ（{len(used_globally)} 語）")
    if dry:
        return
    with io.open(TARGET, "w", encoding="utf-8") as fp:
        fp.write(page_out)


if __name__ == "__main__":
    main()
