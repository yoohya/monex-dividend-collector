"""CSVデータからHTMLページを生成するスクリプト."""

import csv
from collections import defaultdict
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
CSV_PATH = OUTPUT_DIR / "dividend_data.csv"
HTML_PATH = OUTPUT_DIR / "index.html"

FIELDNAMES = [
    "date",
    "timestamp",
    "code",
    "name",
    "dividend_yield_forecast",
    "yield_1y_max",
    "yield_1y_min",
    "yield_1y_avg",
    "yield_2y_max",
    "yield_2y_min",
    "yield_2y_avg",
]

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>配当利回りデータ</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f5f5f5;
    color: #333;
  }}
  h1 {{
    font-size: 1.5rem;
    border-bottom: 2px solid #2c3e50;
    padding-bottom: 8px;
  }}
  h2 {{
    font-size: 1.2rem;
    margin-top: 2rem;
    color: #2c3e50;
  }}
  .updated {{
    color: #666;
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    background: #fff;
    margin-bottom: 2rem;
    font-size: 0.9rem;
  }}
  th, td {{
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: right;
    white-space: nowrap;
  }}
  th {{
    background: #2c3e50;
    color: #fff;
    font-weight: 600;
  }}
  td:nth-child(1), td:nth-child(2) {{
    text-align: left;
  }}
  tr:nth-child(even) {{
    background: #f9f9f9;
  }}
  tr:hover {{
    background: #eef2f7;
  }}
  .container {{
    max-width: 1100px;
    margin: 0 auto;
  }}
  .note {{
    color: #888;
    font-size: 0.8rem;
    margin-top: 1rem;
  }}
</style>
</head>
<body>
<div class="container">
<h1>配当利回りデータ</h1>
<p class="updated">最終更新: {updated}</p>

<h2>最新データ</h2>
<table>
<thead>
<tr>
  <th>銘柄コード</th>
  <th>銘柄名</th>
  <th>予想利回り(%)</th>
  <th>1Y 最大</th>
  <th>1Y 最小</th>
  <th>1Y 平均</th>
  <th>2Y 最大</th>
  <th>2Y 最小</th>
  <th>2Y 平均</th>
</tr>
</thead>
<tbody>
{latest_rows}
</tbody>
</table>

<h2>履歴データ</h2>
<table>
<thead>
<tr>
  <th>日付</th>
  <th>銘柄コード</th>
  <th>銘柄名</th>
  <th>予想利回り(%)</th>
  <th>1Y 最大</th>
  <th>1Y 最小</th>
  <th>1Y 平均</th>
  <th>2Y 最大</th>
  <th>2Y 最小</th>
  <th>2Y 平均</th>
</tr>
</thead>
<tbody>
{history_rows}
</tbody>
</table>

<p class="note">データソース: マネックス銘柄スカウターライト</p>
</div>
</body>
</html>
"""


def _cell(value: str) -> str:
    return value if value else "-"


def generate():
    if not CSV_PATH.exists():
        print(f"CSV not found: {CSV_PATH}")
        return

    rows = []
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print("No data in CSV.")
        return

    # 最新日付のデータを抽出
    latest_date = max(r["date"] for r in rows)
    latest = [r for r in rows if r["date"] == latest_date]
    latest_timestamp = latest[0].get("timestamp", latest_date) if latest else latest_date

    # 最新データテーブル
    latest_lines = []
    for r in latest:
        latest_lines.append(
            f"<tr>"
            f"<td>{_cell(r.get('code', ''))}</td>"
            f"<td>{_cell(r.get('name', ''))}</td>"
            f"<td>{_cell(r.get('dividend_yield_forecast', ''))}</td>"
            f"<td>{_cell(r.get('yield_1y_max', ''))}</td>"
            f"<td>{_cell(r.get('yield_1y_min', ''))}</td>"
            f"<td>{_cell(r.get('yield_1y_avg', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_max', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_min', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_avg', ''))}</td>"
            f"</tr>"
        )

    # 履歴データテーブル（新しい順）
    history_lines = []
    for r in reversed(rows):
        history_lines.append(
            f"<tr>"
            f"<td>{_cell(r.get('date', ''))}</td>"
            f"<td>{_cell(r.get('code', ''))}</td>"
            f"<td>{_cell(r.get('name', ''))}</td>"
            f"<td>{_cell(r.get('dividend_yield_forecast', ''))}</td>"
            f"<td>{_cell(r.get('yield_1y_max', ''))}</td>"
            f"<td>{_cell(r.get('yield_1y_min', ''))}</td>"
            f"<td>{_cell(r.get('yield_1y_avg', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_max', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_min', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_avg', ''))}</td>"
            f"</tr>"
        )

    html = HTML_TEMPLATE.format(
        updated=latest_timestamp,
        latest_rows="\n".join(latest_lines),
        history_rows="\n".join(history_lines),
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {HTML_PATH}")


if __name__ == "__main__":
    generate()
