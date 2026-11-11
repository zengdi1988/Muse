

# Stock Monitor

## Purpose
为用户的 11 只 A 股持仓提供实时行情、最新公告和异动告警能力，支撑盘前简报、收盘日报和盘中监控。不做交易决策，只提供数据。

## Tooling
持仓清单：`config/holdings.json`（11只，含深/沪市代码）。持仓变化时同步更新该文件。

- 实时行情：`python3 bin/quote.py [--json] [--codes sz000408,sh601717]`
  数据源为新浪公开行情接口（需 Referer 头，脚本内已处理，GBK 解码）。
  输出每只的名称、现价、涨跌幅/涨跌额、最高最低、成交量、行情时间。
  停牌或无交易时标注 `停牌/无交易`，不要编造价格。
- 最新公告：`python3 bin/announce.py [--days 3] [--codes 000572] [--json]`
  数据源为东方财富公告接口，默认近 3 天，输出日期、标题和公告原文链接。
- 异动检查：`python3 bin/check_alerts.py [--threshold 5] [--state PATH] [--json]`
  涨跌幅绝对值超过阈值（默认 5%）时输出告警；同代码同日只报一次，
  状态记在 `--state` 文件（默认 `~/workspace/goals/goal/hidden_files/price_alert_state.json`）。
  无异动时只输出 `无异动`。
- 盘前先行指标：`python3 bin/overnight.py`
  数据源为新浪公开行情接口（实时）：富时中国A50期货（隔夜涨跌）、
  中创智领H股 hk00564（AH 联动参考）。输出名称、现价、涨跌幅、行情时间。
  注意：国内期货（碳酸锂主力、沪铝主力）新浪接口不稳定，改用 browser.search 查询。
- 大盘资金流向：`python3 bin/fundflow.py [--json]`
  数据源为东方财富公开接口（无需鉴权）：沪深两市合计主力资金当日净流入净额
  （上证 secid=1.000001 + 深证成指 secid=0.399001 的日 K 资金流末行相加）。
  收盘后即得当日数据，输出自带交易日——以此日期为准，非交易日返回最近交易日数据。
  注意：北向资金日度净流入额自 2024-08-19 起不再公开披露，脚本不伪造方向数字。

## Operating Rules
1. 代码以 `config/holdings.json` 为准，不要凭记忆编造证券代码。
2. 非交易时段行情接口返回的是上一交易日收盘数据，解读时说明时间。
3. 接口失败时如实报错，不编造行情或公告。
4. 公告链接为东方财富原文页，仅供查阅。
## Available connectors

Use `muse.connector_search` to find the current connector docs before following
recovered instructions.
