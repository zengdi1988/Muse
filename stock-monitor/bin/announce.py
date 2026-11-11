#!/usr/bin/env python3
"""上市公司最新公告查询（东方财富公开接口，无需鉴权）。

用法:
    python3 announce.py [--days 3] [--codes 000572,601717] [--json]
默认查询 config/holdings.json 中全部持仓近 --days 天的公告。
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLDINGS_FILE = os.path.join(BASE, "config", "holdings.json")


def load_codes(codes_arg):
    if codes_arg:
        return [c.strip() for c in codes_arg.split(",") if c.strip()]
    with open(HOLDINGS_FILE, encoding="utf-8") as f:
        return [h["code"] for h in json.load(f)]


def fetch_announcements(code, page_size=20):
    params = {
        "sr": "-1", "page_size": str(page_size), "page_index": "1",
        "ann_type": "A", "client_source": "web",
        "stock_list": code, "f_node": "0", "s_node": "0",
    }
    url = ("https://np-anotice-stock.eastmoney.com/api/security/ann?"
           + urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8")
    data = json.loads(raw).get("data", {}).get("list", [])
    out = []
    for a in data:
        codes = a.get("codes") or [{}]
        out.append({
            "code": code,
            "name": codes[0].get("short_name", ""),
            "date": (a.get("notice_date") or "")[:10],
            "title": a.get("title", ""),
            "url": ("https://data.eastmoney.com/notices/detail/%s/%s.html"
                    % (code, a.get("art_code", ""))),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--codes", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cutoff = (datetime.date.today()
              - datetime.timedelta(days=args.days)).isoformat()
    codes = load_codes(args.codes)
    results = []
    for code in codes:
        try:
            anns = fetch_announcements(code)
        except Exception as e:
            print(f"{code} 公告查询失败: {e}", file=sys.stderr)
            continue
        for a in anns:
            if a["date"] >= cutoff:
                results.append(a)
    results.sort(key=lambda x: x["date"], reverse=True)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    if not results:
        print(f"近 {args.days} 天无新公告。")
        return
    for a in results:
        print(f"[{a['date']}] {a['name']}({a['code']}) {a['title']}")
        print(f"  {a['url']}")


if __name__ == "__main__":
    main()
