#!/usr/bin/env python3
"""大盘资金流向查询（东方财富公开接口，无需鉴权）。

两项数据，均为收盘日报「资金流向」板块的可用口径：

1. 主力资金（沪深两市合计）
   上证指数(secid=1.000001) + 深证成指(secid=0.399001) 的当日主力净流入净额相加。
   接口: https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get
   ?lmt=0&klt=101&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59
   &secid=<1.000001|0.399001>
   字段顺序: 日期, 主力净流入净额(元), 小单净额, 中单净额, 大单净额, 超大单净额,
   主力净占比(%), 小单占比, 中单占比, 大单占比, 超大单占比, 收盘价, 涨跌幅(%)
   校验关系: 主力净额 = 超大单净额 + 大单净额。

2. 北向资金
   自2024年8月19日起，北向资金日度净流入额不再公开披露；公开可得的是
   日度成交额和十大成交股。脚本只报告数据所属交易日与可用状态，
   不伪造净流入方向数字。

注意：非交易日接口返回的是最近一个交易日的数据，务必以返回的日期为准，
不要把数字安到当天头上。

用法:
python3 fundflow.py [--json]
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

FFLOW_URL = (
    "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
    "?lmt=0&klt=101&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59"
    "&secid={secid}"
)

# 东方财富 push2his 经常对机房 IP 限流/断连接（RemoteDisconnected），
# 收盘日报需要这组数字，失败时重试几次比直接崩掉更有价值。
MAX_RETRIES = 4
BASE_DELAY = 2.0


def get_json(url):
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Referer": "https://data.eastmoney.com/"}
            )
            raw = urllib.request.urlopen(req, timeout=20).read().decode(
                "utf-8", errors="replace"
            )
            return json.loads(raw)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
                ConnectionError, OSError) as e:
            last_err = e
            delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
    raise RuntimeError("接口请求失败（%d 次重试）: %s" % (MAX_RETRIES, last_err))


def fetch_one(secid):
    data = get_json(FFLOW_URL.format(secid=secid))
    klines = (data.get("data") or {}).get("klines") or []
    if not klines:
        return {"error": "无资金流数据"}
    parts = klines[-1].split(",")
    return {
        "date": parts[0],
        "main_net": float(parts[1]) if len(parts) > 1 else None,
        "main_ratio": float(parts[6]) if len(parts) > 6 else None,
    }


def main_force():
    """返回主力资金数据，金额单位元。"""
    out = {}
    for label, secid in (("sh", "1.000001"), ("sz", "0.399001")):
        try:
            out[label] = fetch_one(secid)
        except RuntimeError as e:
            out[label] = {"error": str(e)}
    dates = {v.get("date") for v in out.values()
             if isinstance(v, dict) and v.get("date")}
    # 两市合计只在两市数据都拿到时才有意义，缺一不可。
    nets = [out[k]["main_net"] for k in ("sh", "sz")
            if out[k].get("main_net") is not None]
    return {
        "date": sorted(dates)[-1] if dates else None,
        "sh_main_net_yuan": out.get("sh", {}).get("main_net"),
        "sz_main_net_yuan": out.get("sz", {}).get("main_net"),
        "total_main_net_yuan": sum(nets) if len(nets) == 2 else None,
        "errors": {k: v["error"] for k, v in out.items() if v.get("error")},
    }


def fmt_yi(v):
    if v is None:
        return "无数据"
    if v >= 0:
        return "净流入 %.1f亿" % (v / 1e8)
    return "净流出 %.1f亿" % (-v / 1e8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    mf = main_force()
    result = {"main_force": mf}

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
        return

    print("(沪深两市合计)")
    errors = mf.get("errors") or {}
    if errors:
        for k, e in errors.items():
            print("资金流接口（%s）暂缺：%s" % (
                "上证" if k == "sh" else "深证", e))
    if mf.get("date"):
        print("交易日: %s" % mf["date"])
        print("上证主力%s；深证主力%s；两市合计%s" % (
            fmt_yi(mf["sh_main_net_yuan"]),
            fmt_yi(mf["sz_main_net_yuan"]),
            fmt_yi(mf["total_main_net_yuan"])))
    else:
        print("两市主力资金数据暂缺。")
    print("")
    print("注：北向资金日度净流入额自2024-08-19起不再公开披露，"
          "收盘日报只报告成交额活跃度口径。")


if __name__ == "__main__":
    main()
