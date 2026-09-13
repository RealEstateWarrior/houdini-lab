"""実験レポートの束ね直し、サイト生成、コミットとプッシュをまとめて行う。

    python publish.py "実験012を追加"

out/ にある *_report.json を番号順に束ねて log_A.pdf を作り直し、
site/ と docs/ を生成して、変更をコミットしてプッシュする。
Gemini Notebook のソース差し替えは、削除を伴うのでここでは行わない。
"""

import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
BUNDLE = os.path.join(OUT, "log_A.pdf")
TITLE = "実験ログ A: プロシージャルモデリング 基礎"


def report_specs():
    """実験番号の順に並べる。001 だけファイル名が box_mountain なので先頭に置く。"""
    specs = []
    for path in glob.glob(os.path.join(OUT, "*_report.json")):
        name = os.path.basename(path)
        if name.startswith("box_mountain"):
            order = 1
        else:
            match = re.match(r"(\d+)_report\.json$", name)
            if not match:
                continue
            order = int(match.group(1))
        specs.append((order, path))
    return [path for _, path in sorted(specs)]


def run(command, **kwargs):
    # 既定の文字コードだと、子プロセスの日本語出力を読むところで落ちる。
    # 子プロセス側の出力も UTF-8 に揃えておかないと、受け取る前に化ける。
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(command, cwd=HERE, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=env, **kwargs)
    if result.returncode != 0:
        raise SystemExit(f"失敗: {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def main():
    message = sys.argv[1] if len(sys.argv) > 1 else "実験ログとサイトを更新"

    specs = report_specs()
    print(f"レポート {len(specs)} 件を束ねる")
    run([sys.executable, "report_pdf.py", "--bundle", BUNDLE, TITLE] + specs)

    # 本文の用語リンクを付け直してから生成する（差し込むのはタグだけ）
    print(run([sys.executable, "link_terms.py"]))
    print(run([sys.executable, "build_site.py"]))

    run(["git", "add", "-A"])
    status = run(["git", "status", "--porcelain"])
    if not status:
        print("変更なし")
        return 0

    run(["git", "-c", "user.name=comeb", "-c", "user.email=fko2547009@gmail.com",
         "commit", "-q", "-m", message])
    run(["git", "push", "-q", "origin", "main"])
    print("プッシュ完了:", run(["git", "log", "--oneline", "-1"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
