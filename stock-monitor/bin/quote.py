#!/usr/bin/env python3
"""A股/ETF 实时行情查询（新浪公开接口，无需鉴权）。

用法:
    python3 quote.py [--json] [--codes sz000408,sh601717]
默认读取 config/holdings.json 中的 11 只持仓。
"""
import argparse
import json
import os
import re
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLDINGS_FILE = os.path.join(BASE, "config", "holdings.json")


def load_holdings(codes_arg):
    if codes_arg:
        out = []
        for c in codes_arg.split(","):
            c = c.strip().lower()
            m = re.match(r"^(sz|sh)(\d{6})$", c)
            if m:
                out.append({"market": m.group(1), "code": m.group(2), "name": c})
        return out
    with open(HOLDINGS_FILE, encoding="utf-8") as f:
        return json.load(f)


def fetch(symbols):
    req = urllib.request.Request(
        "https://hq.sinajs.cn/list=" + ",".join(symbols),
        headers={
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        },
    )
    raw = urllib.request.urlopen(req, timeout=20).read().decode("gbk", errors="replace")
    return raw


def parse(raw, symbols):
    quotes = []
    for sym in symbols:
        m = re.search(r'var hq_str_%s="([^"]*)"' % re.escape(sym), raw)
        if not m or not m.group(1):
            quotes.append({"symbol": sym, "error": "无数据"})
            continue
        f = m.group(1).split(",")
        try:
            name = f[0]
            open_p, prev, cur = float(f[1]), float(f[2]), float(f[3])
            high, low = float(f[4]), float(f[5])
            vol, amount = f[8], f[9]
            date, time = f[30], f[31]
        except (IndexError, ValueError):
            quotes.append({"symbol": sym, "error": "解析失败"})
            continue
        if cur == 0:
            quotes.append({"symbol": sym, "name": name, "suspended": True,
                           "prev_close": prev, "date": date})
            continue
        pct = (cur - prev) / prev * 100 if prev else 0.0
        quotes.append({
            "symbol": sym, "name": name,
            "open": open_p, "prev_close": prev, "price": cur,
            "high": high, "low": low,
            "change_pct": round(pct, 2),
            "change_amt": round(cur - prev, 3),
            "volume": vol, "amount": amount,
            "datetime": f"{date} {time}",
        })
    return quotes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--codes", default="")
    args = ap.parse_args()

    holdings = load_holdings(args.codes)
    symbols = [h["market"] + h["code"] for h in holdings]
    name_map = {h["market"] + h["code"]: h["name"] for h in holdings}
    try:
        raw = fetch(symbols)
    except Exception as e:
        print(f"行情接口请求失败: {e}", file=sys.stderr)
        sys.exit(2)
    quotes = parse(raw, symbols)

    if args.json:
        print(json.dumps(quotes, ensure_ascii=False, indent=2))
        return

    print(f"{'名称':<14}{'代码':<10}{'现价':>8}{'涨跌幅':>9}  时间")
    print("-" * 56)
    for q in quotes:
        label = name_map.get(q["symbol"], q["symbol"])
        if q.get("error"):
            print(f"{label:<14}{q['symbol']:<10}  {q['error']}")
        elif q.get("suspended"):
            print(f"{label:<14}{q['symbol']:<10}  停牌/无交易")
        else:
            sign = "+" if q["change_pct"] >= 0 else ""
            print(f"{label:<14}{q['symbol']:<10}{q['price']:>8.3f}"
                  f"{sign}{q['change_pct']:>8.2f}%  {q['datetime']}")


if __name__ == "__main__":
    main()
