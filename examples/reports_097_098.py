# -*- coding: utf-8 -*-
"""実験097・098 の図とレポートを、測った値から組み立てる。

    python examples/reports_097_098.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "examples"))
OUT = os.path.join(HERE, "out")

from pil_chart import line_chart, PALETTE  # noqa: E402


def stats(no):
    with open(os.path.join(OUT, f"{no}_stats.json"), encoding="utf-8") as fp:
        return json.load(fp)


def write(no, payload):
    with open(os.path.join(OUT, f"{no}_report.json"), "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)
    print("書いた:", f"{no}_report.json")


def do_097():
    data = stats("097")
    rows = data["rows"]
    raw = [r for r in rows if not r["packed"]]
    packed = [r for r in rows if r["packed"]]
    big_raw, big_packed = raw[-1], packed[-1]
    pt_ratio = big_raw["points"] / big_packed["points"]
    time_ratio = big_raw["seconds"] / big_packed["seconds"]
    size_ratio = big_raw["bytes"] / big_packed["bytes"]

    line_chart(
        os.path.join(OUT, "097_pack.png"),
        [{"label": "pack 切 — ファイルの大きさ（MB）",
          "points": [(r["count"], r["mb"]) for r in raw],
          "color": PALETTE[0]},
         {"label": "pack 入 — ファイルの大きさ（MB）",
          "points": [(r["count"], r["mb"]) for r in packed],
          "color": PALETTE[2], "dash": True}],
        title="同じ見た目で、ファイルは約198分の1になる",
        x_label="並べた数", y_label="MB")
    line_chart(
        os.path.join(OUT, "097_time.png"),
        [{"label": "pack 切 — 計算（秒）",
          "points": [(r["count"], r["seconds"]) for r in raw],
          "color": PALETTE[0]},
         {"label": "pack 入 — 計算（秒）",
          "points": [(r["count"], r["seconds"]) for r in packed],
          "color": PALETTE[2], "dash": True},
         {"label": "pack 切 — 書き出し（秒）",
          "points": [(r["count"], r["write_seconds"]) for r in raw],
          "color": PALETTE[1], "dash": True}],
        title="計算も書き出しも、桁が変わる",
        x_label="並べた数", y_label="秒")
    print("097_pack.png 097_time.png")

    write("097", {
        "title": f"pack を入れると、点は{pt_ratio:.0f}分の1・ファイルは{size_ratio:.0f}分の1になる"
                 f" — 1万個で 22.5MB が 0.114MB",
        "summary":
            "copytopoints の「Pack and Instance」は軽くなると言われる。"
            "どこがどれだけ軽くなるのかを、3つの数で測った。持っている点と面の数、"
            "計算にかかる時間、ディスクに書いたときのファイルの大きさ。\n\n"
            f"複製する形は球（{data['unit_points']}点・{data['unit_prims']}面）。"
            "板の上に 100 / 1,000 / 10,000 個並べた。\n\n"
            f"1万個のとき、pack を切ると {big_raw['points']:,}点・{big_raw['prims']:,}面。"
            f"入れると {big_packed['points']:,}点・{big_packed['prims']:,}面で、"
            f"**点の数は {pt_ratio:.0f}分の1**。複製1つが1点になるので、"
            "並べた数がそのまま点の数になる。\n\n"
            f"計算は {big_raw['seconds']}秒 から {big_packed['seconds']}秒へ。"
            f"**{time_ratio:.0f}倍速い。** 書き出しは "
            f"{big_raw['write_seconds']}秒 から {big_packed['write_seconds']}秒。\n\n"
            f"ファイルは {big_raw['mb']}MB から {big_packed['mb']}MB。"
            f"**{size_ratio:.0f}分の1。** 中身を1つだけ持ち、あとは置き場所だけを"
            "並べているので、数を増やしても増え方がゆるい。\n\n"
            "代わりに、中身を直接触れなくなる。点や面を選んで動かしたいときは "
            "unpack で開く必要があり、そこで軽さは失われる。",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "pack の入／切で、点・面・時間・ファイルの大きさ",
             "note": f"複製する形は球（20×20、{data['unit_points']}点・"
                     f"{data['unit_prims']}面）。並べ先は 10×10 の板に scatter で散らした点。"
                     "ファイルの大きさは .bgeo.sc に書いて測り、そのあと消した。",
             "images": [{"path": "097_pack.png",
                         "caption": "ファイルの大きさは桁が変わる。1万個で 22.5MB が 0.114MB。"},
                        {"path": "097_time.png",
                         "caption": "計算も書き出しも、pack を入れるとほぼ平らなまま。"}],
             "per_row": 2,
             "columns": ["並べた数", "pack", "点", "面", "計算 秒", "書き出し 秒", "MB"],
             "rows": [[f"{r['count']:,}", "入" if r["packed"] else "切",
                       f"{r['points']:,}", f"{r['prims']:,}",
                       f"{r['seconds']:.3f}", f"{r['write_seconds']:.3f}",
                       str(r["mb"])] for r in rows]},
        ],
        "notes": [
            f"<strong>点の数は並べた数と同じになる。</strong>1万個で "
            f"{big_raw['points']:,}点 → {big_packed['points']:,}点、"
            f"{pt_ratio:.0f}分の1。複製1つが1点として扱われる。",
            f"<strong>ファイルは{size_ratio:.0f}分の1。</strong>"
            f"{big_raw['mb']}MB → {big_packed['mb']}MB。"
            "中身を1つだけ持ち、残りは置き場所だけを並べている。",
            f"<strong>計算は{time_ratio:.0f}倍速い。</strong>"
            f"{big_raw['seconds']}秒 → {big_packed['seconds']}秒。"
            f"書き出しも {big_raw['write_seconds']}秒 → {big_packed['write_seconds']}秒。",
            "<strong>代わりに中身を触れなくなる。</strong>点や面を選んで動かすには "
            "unpack で開く必要があり、そこで軽さは失われる。"
            "並べたあと形を変えないなら、入れておいて損はない。",
        ],
        "next": [
            "unpack で開いたとき、元の重さに戻るのか（それ以上になるのか）",
            "pack したまま、まとめて色や大きさを変えられる範囲はどこまでか",
        ],
    })


def do_098():
    data = stats("098")
    rows = data["rows"]
    cols_rows = data["cols_rows"]
    circle = data["circle"]
    expect = data["ngon_expect"]
    bool_row = [r for r in rows if r["way"] == "boolean"][0]
    cookie_row = [r for r in rows if r["way"] == "cookie"][0]
    vdb_rows = [r for r in rows if r["way"] == "vdb"]

    line_chart(
        os.path.join(OUT, "098_hole.png"),
        [{"label": "VDB の、n角形の答えとの差",
          "points": [(i + 1, abs(r["vs_ngon"]) * 1e6)
                     for i, r in enumerate(vdb_rows)],
          "color": PALETTE[0]},
         {"label": "boolean の差（0）",
          "points": [(1, 0.0), (len(vdb_rows), 0.0)],
          "color": PALETTE[2], "dash": True}],
        title="升目を半分にするごとに、VDB の差は約半分になる",
        x_label="升目を半分にした回数", y_label="答えとの差 ×100万")
    line_chart(
        os.path.join(OUT, "098_ngon.png"),
        [{"label": "boolean で出た体積",
          "points": [(r["cols"], r["volume"]) for r in cols_rows],
          "color": PALETTE[0]},
         {"label": "n角形で考えた答え",
          "points": [(r["cols"], r["expect"]) for r in cols_rows],
          "color": PALETTE[1], "dash": True},
         {"label": "円で考えた答え",
          "points": [(cols_rows[0]["cols"], circle),
                     (cols_rows[-1]["cols"], circle)],
          "color": PALETTE[4], "dash": True}],
        title="boolean は n角形の答えとぴったり重なる（4通りすべてで差 0.000000）",
        x_label="円柱の辺の数", y_label="体積")
    print("098_hole.png 098_ngon.png")

    write("098", {
        "title": "boolean は答えと6桁まで一致する — 差の正体は円ではなく多角形だった",
        "summary":
            "1辺 1.0 の箱に、半径 0.25 の円柱の穴を通す。答えは計算で出せる。"
            f"円で考えれば {circle}。ただし Houdini の円柱は多角形なので、"
            f"80角形で考えた答えは {expect} になる。\n\n"
            "この「答えの分かっている形」を3通りで作って、体積を突き合わせた。\n\n"
            f"boolean と cookie は、どちらも {bool_row['volume']}。"
            f"**80角形の答えとの差は {bool_row['vs_ngon']:+.6f}**、つまり6桁まで一致する。"
            f"円の答えとの差 {bool_row['vs_circle']:+.6f} は、"
            "アルゴリズムのずれではなく多角形近似そのものだった。\n\n"
            "念のため、円柱の辺の数を 12 / 40 / 80 / 200 と変えて確かめた。"
            "4通りすべてで、出た体積は n角形の答えと差 0.000000 で一致した。"
            f"辺を増やすほど円の答えに近づく（12角形で {cols_rows[0]['vs_circle']:+.6f}、"
            f"200角形で {cols_rows[-1]['vs_circle']:+.6f}）。\n\n"
            f"VDB は升目の細かさで決まる。升目 {vdb_rows[0]['detail'].split()[-1]} で "
            f"{vdb_rows[0]['vs_ngon']:+.6f}、半分にするごとに差も約半分になり、"
            f"{vdb_rows[-1]['detail'].split()[-1]} で {vdb_rows[-1]['vs_ngon']:+.6f}。"
            f"ただし面の数は {vdb_rows[-1]['prims']:,} で、boolean の "
            f"{bool_row['prims']} 面に対して桁が違う。"
            "**平らな面で足りる形に VDB を使うと、精度で負けて重さで負ける。**",
        "graph": "",
        "graph_image": "",
        "comparisons": [
            {"label": "3つの道筋の結果（円柱は80角形）",
             "note": f"箱は poly の 6面、円柱は poly の 82面。"
                     f"「n角形との差」は 80角形で考えた答え {expect} との差、"
                     f"「円との差」は円で考えた答え {circle} との差。",
             "images": [{"path": "098_hole.png",
                         "caption": "VDB の差は升目を半分にするごとに約半分。"
                                    "boolean は最初から差が無い。"}],
             "per_row": 1,
             "columns": ["道筋", "細かさ", "面", "秒", "体積",
                         "n角形との差", "円との差"],
             "rows": [[r["way"], r["detail"], f"{r['prims']:,}",
                       f"{r['seconds']:.3f}", f"{r['volume']:.6f}",
                       f"{r['vs_ngon']:+.6f}", f"{r['vs_circle']:+.6f}"]
                      for r in rows]},
            {"label": "円柱の辺の数を変える（boolean）",
             "note": "辺の数 n を変えると、答えも n角形の式で変わる。"
                     "出た値がその式を追うかを見た。",
             "images": [{"path": "098_ngon.png",
                         "caption": "4通りすべてで、答えの線と完全に重なっている。"}],
             "per_row": 1,
             "columns": ["辺の数", "面", "体積", "n角形の答え", "差", "円との差"],
             "rows": [[str(r["cols"]), f"{r['prims']:,}", f"{r['volume']:.6f}",
                       f"{r['expect']:.6f}", f"{r['vs_ngon']:+.6f}",
                       f"{r['vs_circle']:+.6f}"] for r in cols_rows]},
        ],
        "notes": [
            "<strong>boolean と cookie は答えと6桁まで一致する。</strong>"
            f"どちらも {bool_row['volume']}、80角形の答えとの差は "
            f"{bool_row['vs_ngon']:+.6f}。cookie は "
            f"{cookie_row['seconds']}秒、boolean は {bool_row['seconds']}秒だった。",
            "<strong>円との差は多角形近似のぶん。</strong>"
            f"12角形で {cols_rows[0]['vs_circle']:+.6f}、200角形で "
            f"{cols_rows[-1]['vs_circle']:+.6f}。"
            "アルゴリズムを疑う前に、円柱の辺の数を見るほうが早い。",
            "<strong>VDB は精度でも重さでも負ける（この形では）。</strong>"
            f"升目 {vdb_rows[-1]['detail'].split()[-1]} で差 "
            f"{vdb_rows[-1]['vs_ngon']:+.6f}、面は {vdb_rows[-1]['prims']:,}。"
            f"boolean は {bool_row['prims']}面で差 {bool_row['vs_ngon']:+.6f}。"
            "平らな面で表せる形なら、VDB を通す理由は無い。",
            "<strong>つまずいた点。</strong>箱と円柱の Primitive Type を "
            "poly 以外（mesh / polymesh）にすると、boolean も cookie も"
            "<strong>黙って何もしない</strong>。エラーも警告も出ず、箱がそのまま出てくる。"
            "最初これに気づかず、体積 1.000000 のまま「差 +24%」という表を作ってしまった。"
            "答えの分かっている形で試していたから気づけた。",
        ],
        "next": [
            "曲面（球どうし）の引き算では、どの道筋がいちばん答えに近いか",
            "面が重なっている・接しているときに boolean が崩れる条件",
            "VDB の差が升目の1乗で減るのか2乗で減るのか（もっと細かくして確かめる）",
        ],
    })


if __name__ == "__main__":
    do_097()
    do_098()
