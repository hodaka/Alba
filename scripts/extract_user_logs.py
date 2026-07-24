#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_user_logs.py — 会話ログ（ユーザー発言）無加工蓄積スクリプト

Claude Code の JSONL トランスクリプトから **user ロールの生発言のみ** を抽出し、
リポジトリの logs/YYYY-MM-DD.md に追記する。

方針:
  - 抽出テキストは一切加工しない（整形・要約・句読点調整・誤字修正、すべて禁止）。
    本文はソースの文字列をそのまま書き出す。
  - user メッセージのうち content が「文字列」のものだけを発言とみなす。
    content が list（tool_result 等）のもの、isMeta のものは発言ではないので除外する。
  - uuid を状態ファイル(logs/.processed_uuids)で管理し、Stop フック等で
    何度実行されても同じ発言を二重追記しない。

実行方法:
  1) Stop フック: stdin に渡される JSON の transcript_path を処理する。
  2) 手動実行:   引数に JSONL パスを渡す、または cwd から ~/.claude/projects/<enc> を解決して
                 その配下の *.jsonl をすべて処理する。
"""

import sys
import os
import json
import glob
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(REPO_ROOT, "logs")
STATE_FILE = os.path.join(LOGS_DIR, ".processed_uuids")


def project_jsonl_dir_for_cwd():
    """cwd に対応する ~/.claude/projects/<encoded> ディレクトリを返す。"""
    home = os.path.expanduser("~")
    # Claude Code は cwd のパス区切りを '-' に置換してディレクトリ名にする
    encoded = os.path.abspath(REPO_ROOT).replace(os.sep, "-")
    return os.path.join(home, ".claude", "projects", encoded)


def resolve_source_files():
    """処理対象の JSONL ファイル一覧を決める。"""
    # 1) Stop フック: stdin の JSON から transcript_path を取る
    transcript = None
    if not sys.stdin.isatty():
        try:
            data = sys.stdin.read()
            if data.strip():
                payload = json.loads(data)
                transcript = payload.get("transcript_path")
        except Exception:
            transcript = None
    if transcript and os.path.isfile(transcript):
        return [transcript]

    # 2) 引数指定
    args = [a for a in sys.argv[1:] if os.path.isfile(a)]
    if args:
        return args

    # 3) cwd から解決してディレクトリ内の全 JSONL
    d = project_jsonl_dir_for_cwd()
    if os.path.isdir(d):
        return sorted(glob.glob(os.path.join(d, "*.jsonl")))
    return []


def load_state():
    seen = set()
    if os.path.isfile(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                u = line.strip()
                if u:
                    seen.add(u)
    return seen


def is_user_utterance(obj):
    """生のユーザー発言なら (uuid, timestamp, text) を、そうでなければ None を返す。"""
    if obj.get("type") != "user":
        return None
    if obj.get("isMeta") is True:
        return None
    msg = obj.get("message")
    if not isinstance(msg, dict):
        return None
    if msg.get("role") != "user":
        return None
    content = msg.get("content")
    # content が文字列のものだけが生発言。list（tool_result 等）は発言ではない。
    if not isinstance(content, str):
        return None
    uuid = obj.get("uuid")
    if not uuid:
        return None
    return uuid, obj.get("timestamp"), content


def date_key(ts):
    """ISO タイムスタンプからローカル日付 YYYY-MM-DD を得る。取れなければ本日日付。"""
    if ts:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.astimezone().strftime("%Y-%m-%d"), dt.astimezone().strftime("%H:%M:%S")
        except Exception:
            pass
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


def main():
    sources = resolve_source_files()
    if not sources:
        print("[extract_user_logs] 対象 JSONL が見つからない。何もしない。")
        return 0

    seen = load_state()
    # 追記対象を (uuid, ts, text) で収集（ソース順＝時系列）
    new_items = []
    new_uuids = []
    for path in sources:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    res = is_user_utterance(obj)
                    if not res:
                        continue
                    uuid, ts, text = res
                    if uuid in seen:
                        continue
                    seen.add(uuid)
                    new_items.append((uuid, ts, text))
                    new_uuids.append(uuid)
        except FileNotFoundError:
            continue

    if not new_items:
        print("[extract_user_logs] 新規のユーザー発言なし。")
        return 0

    os.makedirs(LOGS_DIR, exist_ok=True)

    # 日付ごとに追記。本文は一切加工せずそのまま書き出す。
    count = 0
    for uuid, ts, text in new_items:
        day, hms = date_key(ts)
        out_path = os.path.join(LOGS_DIR, "%s.md" % day)
        new_file = not os.path.exists(out_path)
        with open(out_path, "a", encoding="utf-8") as w:
            if new_file:
                w.write("# %s 会話ログ（ユーザー発言・無加工）\n" % day)
            w.write("\n## %s\n\n" % hms)
            w.write(text)          # ← 本文はソースのまま。改変しない。
            if not text.endswith("\n"):
                w.write("\n")
        count += 1

    # 状態ファイルに追記（uuid のみ）
    with open(STATE_FILE, "a", encoding="utf-8") as s:
        for uuid in new_uuids:
            s.write(uuid + "\n")

    print("[extract_user_logs] %d 件のユーザー発言を logs/ に追記した。" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
