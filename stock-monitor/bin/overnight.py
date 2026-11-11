#!/usr/bin/env python3
"""隔夜/盘前先行指标：富时中国A50期货 + 中创智领H股(00564)。

数据源：新浪公开行情接口（需 Referer，否则 403）。
A50 期货为境外交易，A股盘前可看其隔夜涨跌；H股 00564 为中创智领港股，
港股交易时段与A股基本重合，可作 AH 联动参考。

用法：python3 bin/overnight.py
"""
import re
import urllib.request

CODES = [
    ("hf_CHA50CFD", "富时A50期货"),
    ("hk00564", "中创智领H股"),
]

URL = "https://hq.sinajs.cn/list=" + ",".join(c for c, _ in CODES)


def fetch():
    req = urllib.request.Request(URL, headers={"Referer": "https://finance.sina.com.cn"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("GBK", errors="ignore")


def parse_a50(line):
    # hf_CHA50CFD: 现价,,买价,卖价,最高,最低,时间,?,昨收,...,日期,名称,...
    m = re.search(r'="([^"]*)"', line)
    f = m.group(1).split(",")
    price, prev = float(f[0]), float(f[8])
    chg = (price - prev) / prev * 100 if prev else 0.0
    return ("富时A50期货", "hf_CHA50CFD", price, chg, f[12] + " " + f[6])


def parse_hk(line):
    # hk: 英文名,中文名,今开,昨收,最高,最低,现价,涨跌,涨跌幅%,买一,卖一,成交量,成交额,...,日期,时间
    m = re.search(r'="([^"]*)"', line)
    f = m.group(1).split(",")
    return (f[1], "hk00564", float(f[6]), float(f[8]), f[17] + " " + f[18])


def main():
    text = fetch()
    lines = [l for l in text.strip().splitlines() if l.strip()]
    rows = []
    for line in lines:
        if "hf_CHA50CFD" in line:
            rows.append(parse_a50(line))
        elif "hk00564" in line:
            rows.append(parse_hk(line))
    print(f"{'名称':<14}{'代码':<12}{'现价':>10}{'涨跌幅':>9}  时间")
    print("-" * 58)
    for name, code, price, chg, t in rows:
        flag = "+" if chg > 0 else ""
        print(f"{name:<14}{code:<12}{price:>10.2f}{flag}{chg:>8.2f}%  {t}")


if __name__ == "__main__":
    main()
