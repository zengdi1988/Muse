#!/usr/bin/env python3
"""盘中异动检查：持仓涨跌幅超过阈值时输出告警（同代码同日只报一次）。

用法:
    python3 check_alerts.py [--threshold 5] [--state PATH] [--json]
无异动时只输出一行"无异动"。
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quote import load_holdings, fetch, parse  # noqa: E402

DEFAULT_STATE = os.path.expanduser(
    "~/workspace/goals/goal/hidden_files/price_alert_state.json")


def load_state(path, today):
    state = {"date": today, "alerted": []}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                saved = json.load(f)
            if saved.get("date") == today:
                state = saved
        except Exception:
            pass
    return state


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=5.0)
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    state = load_state(args.state, today)

    holdings = load_holdings("")
    symbols = [h["market"] + h["code"] for h in holdings]
    name_map = {h["market"] + h["code"]: h["name"] for h in holdings}
    try:
        quotes = parse(fetch(symbols), symbols)
    except Exception as e:
        print("行情接口请求失败: %s" % e, file=sys.stderr)
        sys.exit(2)

    alerts = []
    for q in quotes:
        if q.get("error") or q.get("suspended"):
            continue
        crossed = abs(q["change_pct"]) >= args.threshold
        if crossed and q["symbol"] not in state["alerted"]:
            alerts.append({
                "symbol": q["symbol"],
                "name": name_map.get(q["symbol"], q["symbol"]),
                "price": q["price"],
                "change_pct": q["change_pct"],
                "change_amt": q["change_amt"],
                "datetime": q["datetime"],
            })
            state["alerted"].append(q["symbol"])

    save_state(args.state, state)

    if args.json:
        print(json.dumps(alerts, ensure_ascii=False, indent=2))
        return
    if not alerts:
        print("无异动")
        return
    for a in alerts:
        direction = "涨" if a["change_pct"] >= 0 else "跌"
        print("【异动】%s(%s) %s %+.2f%%，现价 %.3f（%s）" % (
            a["name"], a["symbol"], direction,
            a["change_pct"], a["price"], a["datetime"]))


if __name__ == "__main__":
    main()
