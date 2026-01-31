"""マネックス銘柄スカウターライトから予想配当利回り統計を収集するスクリプト."""

import asyncio
import csv
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from playwright.async_api import async_playwright

BASE_URL = "https://scouter.monex.co.jp/report/index"
OUTPUT_DIR = Path(__file__).parent / "output"
STOCKS_FILE = Path(__file__).parent / "stocks.json"

# 予想配当利回り（会社予想ベース）チャートのインデックス
YIELD_CHART_INDEX = 3

JS_EXTRACT_PLOT_LINES = """(chartIndex) => {
    const containers = document.querySelectorAll('.highcharts-container');
    if (chartIndex >= containers.length) return null;
    const parent = containers[chartIndex].parentElement;
    const chart = jQuery(parent).highcharts();
    if (!chart) return null;

    const result = {};
    if (chart.yAxis) {
        for (const axis of chart.yAxis) {
            if (axis.plotLinesAndBands) {
                for (const pl of axis.plotLinesAndBands) {
                    const id = pl.options ? pl.options.id : '';
                    const value = pl.options ? pl.options.value : null;
                    if (id === 'plotLineMax') result.max = value;
                    if (id === 'plotLineMin') result.min = value;
                    if (id === 'plotLineAvg') result.avg = value;
                }
            }
        }
    }
    return result;
}"""

JS_CLICK_PERIOD = """({chartIndex, buttonIndex}) => {
    const containers = document.querySelectorAll('.highcharts-container');
    if (chartIndex >= containers.length) return false;
    const parent = containers[chartIndex].parentElement;
    const chart = jQuery(parent).highcharts();
    if (!chart || !chart.rangeSelector || !chart.rangeSelector.clickButton) return false;
    chart.rangeSelector.clickButton(buttonIndex, true);
    return true;
}"""

JS_GET_CURRENT_YIELD = """() => {
    // サマリーセクションから予想配当利回りを取得
    const summary = document.querySelector('.summary');
    if (!summary) return null;
    const ths = summary.querySelectorAll('th');
    for (const th of ths) {
        if (th.textContent.includes('配当利回り')) {
            const td = th.nextElementSibling;
            if (!td) continue;
            const num = td.querySelector('.num');
            if (num) {
                const text = num.textContent.trim();
                if (text && text !== '－') return text;
            }
        }
    }
    return null;
}"""

JS_GET_SUMMARY_VALUES = """() => {
    // サマリーセクションからPER・PBRを取得
    const summary = document.querySelector('.summary');
    if (!summary) return {};
    const result = {};
    const ths = summary.querySelectorAll('th');
    for (const th of ths) {
        const text = th.textContent;
        const td = th.nextElementSibling;
        if (!td) continue;
        const num = td.querySelector('.num');
        if (!num) continue;
        const v = num.textContent.trim();
        if (!v || v === '--' || v === '－') continue;
        if (text.includes('PER')) result.per = v;
        if (text.includes('PBR')) result.pbr = v;
    }
    return result;
}"""

JS_GET_STOCK_PRICE = """() => {
    // div.latest_stock_price から現在値を取得
    const el = document.querySelector('.latest_stock_price');
    if (!el) return null;
    const m = el.textContent.match(/([\\d,]+\\.?\\d*)\\s*円/);
    return m ? m[1] : null;
}"""

JS_EXTRACT_YIELD_HISTORY = """(chartIndex) => {
    const containers = document.querySelectorAll('.highcharts-container');
    if (chartIndex >= containers.length) return null;
    const parent = containers[chartIndex].parentElement;
    const chart = jQuery(parent).highcharts();
    if (!chart || !chart.series || chart.series.length < 2) return null;
    const data = chart.series[1].data;
    if (!data || data.length === 0) return null;
    const last = data[data.length - 1];
    const prev1 = data.length >= 2 ? data[data.length - 2] : null;
    const prev5 = data.length >= 6 ? data[data.length - 6] : null;
    return {
        current: last ? last.y : null,
        prev1d: prev1 ? prev1.y : null,
        prev5d: prev5 ? prev5.y : null
    };
}"""


def load_stocks() -> list[dict]:
    with open(STOCKS_FILE, encoding="utf-8") as f:
        return json.load(f)


async def fetch_dividend_stats(page, code: str) -> dict:
    """銘柄スカウターライトから配当利回り統計を取得する."""
    url = f"{BASE_URL}/{code}"
    await page.goto(url, wait_until="networkidle")

    data = {"code": code}

    # 現在の予想配当利回りをHTMLサマリーから取得
    current_yield = await page.evaluate(JS_GET_CURRENT_YIELD)
    if current_yield:
        data["dividend_yield_forecast"] = current_yield

    # 株価をHTMLサマリーから取得
    price = await page.evaluate(JS_GET_STOCK_PRICE)
    if price:
        data["price"] = price

    # PER・PBRを取得
    summary = await page.evaluate(JS_GET_SUMMARY_VALUES)
    if summary.get("per"):
        data["per"] = summary["per"]
    if summary.get("pbr"):
        data["pbr"] = summary["pbr"]

    # 利回りの前日比・前週比を取得（2年チャートのseriesデータから）
    yield_history = await page.evaluate(JS_EXTRACT_YIELD_HISTORY, YIELD_CHART_INDEX)
    if yield_history:
        current = yield_history.get("current")
        prev1d = yield_history.get("prev1d")
        prev5d = yield_history.get("prev5d")
        if current is not None and prev1d is not None:
            data["yield_1d_change"] = round(current - prev1d, 2)
        if current is not None and prev5d is not None:
            data["yield_1w_change"] = round(current - prev5d, 2)

    # 2年データ（デフォルト表示）を取得
    stats_2y = await page.evaluate(JS_EXTRACT_PLOT_LINES, YIELD_CHART_INDEX)
    if stats_2y:
        data["yield_2y_max"] = stats_2y.get("max")
        data["yield_2y_min"] = stats_2y.get("min")
        data["yield_2y_avg"] = (
            round(stats_2y["avg"], 2) if stats_2y.get("avg") is not None else None
        )

    # 1年に切り替え
    clicked = await page.evaluate(
        JS_CLICK_PERIOD, {"chartIndex": YIELD_CHART_INDEX, "buttonIndex": 0}
    )
    if clicked:
        await page.wait_for_timeout(500)
        stats_1y = await page.evaluate(JS_EXTRACT_PLOT_LINES, YIELD_CHART_INDEX)
        if stats_1y:
            data["yield_1y_max"] = stats_1y.get("max")
            data["yield_1y_min"] = stats_1y.get("min")
            data["yield_1y_avg"] = (
                round(stats_1y["avg"], 2) if stats_1y.get("avg") is not None else None
            )

    return data


async def run():
    stocks = load_stocks()
    OUTPUT_DIR.mkdir(exist_ok=True)

    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    today = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    csv_path = OUTPUT_DIR / "dividend_data.csv"
    file_exists = csv_path.exists()

    fieldnames = [
        "date",
        "timestamp",
        "code",
        "name",
        "sector",
        "price",
        "per",
        "pbr",
        "dividend_yield_forecast",
        "yield_1d_change",
        "yield_1w_change",
        "yield_1y_max",
        "yield_1y_min",
        "yield_1y_avg",
        "yield_2y_max",
        "yield_2y_min",
        "yield_2y_avg",
    ]

    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for stock in stocks:
            code = stock["code"]
            name = stock["name"]
            print(f"Fetching {code} ({name})...")
            sector = stock.get("sector", "")
            try:
                data = await fetch_dividend_stats(page, code)
                data["name"] = name
                data["sector"] = sector
                data["date"] = today
                data["timestamp"] = timestamp
                results.append(data)
            except Exception as e:
                print(f"  ERROR: {e}", file=sys.stderr)
                results.append({
                    "date": today,
                    "timestamp": timestamp,
                    "code": code,
                    "name": name,
                    "sector": sector,
                })
            await asyncio.sleep(1)  # サーバー負荷軽減

        await browser.close()

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. {len(results)} records appended to {csv_path}")

    # 結果サマリーを表示
    for r in results:
        y = r.get("dividend_yield_forecast", "N/A")
        y1 = f"{r.get('yield_1y_min', '?')}-{r.get('yield_1y_max', '?')}(avg {r.get('yield_1y_avg', '?')})"
        y2 = f"{r.get('yield_2y_min', '?')}-{r.get('yield_2y_max', '?')}(avg {r.get('yield_2y_avg', '?')})"
        print(f"  {r.get('code')} {r.get('name')}: 利回り(予)={y}%, 1Y={y1}%, 2Y={y2}%")


if __name__ == "__main__":
    asyncio.run(run())
