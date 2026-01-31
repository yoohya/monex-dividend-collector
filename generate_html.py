"""CSVデータからHTMLページを生成するスクリプト."""

import csv
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
CSV_PATH = OUTPUT_DIR / "dividend_data.csv"
HTML_PATH = OUTPUT_DIR / "index.html"

FIELDNAMES = [
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
    cursor: pointer;
    user-select: none;
  }}
  th .sort-arrow {{
    margin-left: 4px;
    font-size: 0.7rem;
  }}
  td:nth-child(1), td:nth-child(2), td:nth-child(3) {{
    text-align: left;
  }}
  tr.yield-4 {{
    background: #f8d7da;
  }}
  tr.yield-3 {{
    background: #ffe0b2;
  }}
  tr.yield-2 {{
    background: #fff3cd;
  }}
  tr.yield-1 {{
    background: #fff9e6;
  }}
  tr:hover {{
    filter: brightness(0.95);
  }}
  .container {{
    max-width: 1200px;
    margin: 0 auto;
  }}
  .controls {{
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    align-items: center;
  }}
  .legend {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .legend label {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
  }}
  .legend i {{
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 1px solid #ccc;
    border-radius: 2px;
    font-style: normal;
  }}
  .col-toggles {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    border-left: 1px solid #ccc;
    padding-left: 16px;
  }}
  .col-toggles label {{
    cursor: pointer;
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
<div class="controls">
  <div class="legend" id="yield-filter">
    <label><input type="checkbox" checked data-yield="yield-4"><i style="background:#f8d7da"></i> 1Y・2Y両方の最大以上</label>
    <label><input type="checkbox" checked data-yield="yield-3"><i style="background:#ffe0b2"></i> いずれかの最大以上</label>
    <label><input type="checkbox" checked data-yield="yield-2"><i style="background:#fff3cd"></i> 1Y・2Y両方の平均以上</label>
    <label><input type="checkbox" checked data-yield="yield-1"><i style="background:#fff9e6"></i> いずれかの平均以上</label>
    <label><input type="checkbox" checked data-yield="yield-0"><i style="background:#fff;border:1px solid #ccc"></i> 平均未満</label>
  </div>
  <div class="col-toggles" id="col-toggles"></div>
</div>

<table class="sortable">
<thead>
<tr>
  <th>銘柄コード</th>
  <th>銘柄名</th>
  <th>セクター</th>
  <th>株価</th>
  <th>PER</th>
  <th>PBR</th>
  <th>予想利回り(%)</th>
  <th>前日比</th>
  <th>前週比</th>
  <th>1Y 最小</th>
  <th>1Y 平均</th>
  <th>1Y 最大</th>
  <th>2Y 最小</th>
  <th>2Y 平均</th>
  <th>2Y 最大</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>

<p class="note">データソース: マネックス銘柄スカウターライト</p>
</div>
<script>
(function() {{
  document.querySelectorAll('table.sortable').forEach(function(table) {{
    var headers = table.querySelectorAll('thead th');
    var sortState = {{}};
    headers.forEach(function(th, colIndex) {{
      th.addEventListener('click', function() {{
        var tbody = table.querySelector('tbody');
        var rows = Array.from(tbody.querySelectorAll('tr'));
        var ascending = sortState[colIndex] !== 'asc';
        sortState[colIndex] = ascending ? 'asc' : 'desc';
        // 他の列のソート状態をリセット
        Object.keys(sortState).forEach(function(k) {{
          if (parseInt(k) !== colIndex) delete sortState[k];
        }});
        rows.sort(function(a, b) {{
          var cellA = a.cells[colIndex].textContent.trim();
          var cellB = b.cells[colIndex].textContent.trim();
          // "-" を空として扱う
          if (cellA === '-') cellA = '';
          if (cellB === '-') cellB = '';
          // 数値判定（カンマ除去）
          var numA = parseFloat(cellA.replace(/,/g, ''));
          var numB = parseFloat(cellB.replace(/,/g, ''));
          var result;
          if (!isNaN(numA) && !isNaN(numB)) {{
            result = numA - numB;
          }} else if (!isNaN(numA)) {{
            result = -1;
          }} else if (!isNaN(numB)) {{
            result = 1;
          }} else {{
            result = cellA.localeCompare(cellB, 'ja');
          }}
          return ascending ? result : -result;
        }});
        rows.forEach(function(row) {{ tbody.appendChild(row); }});
        // 矢印を更新
        headers.forEach(function(h, i) {{
          var arrow = h.querySelector('.sort-arrow');
          if (!arrow) {{
            arrow = document.createElement('span');
            arrow.className = 'sort-arrow';
            h.appendChild(arrow);
          }}
          if (i === colIndex) {{
            arrow.textContent = ascending ? ' \\u25B2' : ' \\u25BC';
          }} else {{
            arrow.textContent = '';
          }}
        }});
      }});
    }});
  }});
}})();

  // 利回りレベルによる行フィルタ
  (function() {{
    var checkboxes = document.querySelectorAll('#yield-filter input[type="checkbox"]');
    checkboxes.forEach(function(cb) {{
      cb.addEventListener('change', function() {{
        var cls = cb.getAttribute('data-yield');
        var rows = document.querySelectorAll('tbody tr.' + cls);
        var display = cb.checked ? '' : 'none';
        rows.forEach(function(row) {{ row.style.display = display; }});
      }});
    }});
  }})();

  // 列の表示/非表示トグル
  (function() {{
    var table = document.querySelector('table.sortable');
    if (!table) return;
    var headers = table.querySelectorAll('thead th');
    var container = document.getElementById('col-toggles');
    var hiddenByDefault = ['PER', 'PBR', '1Y 最小', '2Y 最小'];
    headers.forEach(function(th, colIndex) {{
      var headerText = th.textContent.trim();
      var label = document.createElement('label');
      var cb = document.createElement('input');
      cb.type = 'checkbox';
      var hidden = hiddenByDefault.indexOf(headerText) !== -1;
      cb.checked = !hidden;
      if (hidden) {{
        table.querySelectorAll('tr').forEach(function(row) {{
          if (row.cells[colIndex]) row.cells[colIndex].style.display = 'none';
        }});
      }}
      cb.addEventListener('change', function() {{
        var display = cb.checked ? '' : 'none';
        table.querySelectorAll('tr').forEach(function(row) {{
          if (row.cells[colIndex]) row.cells[colIndex].style.display = display;
        }});
      }});
      label.appendChild(cb);
      label.appendChild(document.createTextNode(' ' + headerText));
      container.appendChild(label);
    }});
  }})();
</script>
</body>
</html>
"""


def _cell(value: str) -> str:
    return value if value else "-"


def _change_cell(value: str | None) -> str:
    if not value:
        return '<td style="color:#999">-</td>'
    try:
        v = float(value)
    except ValueError:
        return '<td style="color:#999">-</td>'
    if v > 0:
        return f'<td style="color:#2e7d32">+{value}</td>'
    if v < 0:
        return f'<td style="color:#c62828">{value}</td>'
    return f'<td style="color:#999">{value}</td>'


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def _row_class(r: dict) -> str:
    current = _to_float(r.get("dividend_yield_forecast"))
    if current is None:
        return ' class="yield-0"'
    y1_max = _to_float(r.get("yield_1y_max"))
    y2_max = _to_float(r.get("yield_2y_max"))
    y1_avg = _to_float(r.get("yield_1y_avg"))
    y2_avg = _to_float(r.get("yield_2y_avg"))

    maxes = [v for v in (y1_max, y2_max) if v is not None]
    avgs = [v for v in (y1_avg, y2_avg) if v is not None]

    if maxes and current >= max(maxes):
        return ' class="yield-4"'
    if maxes and current >= min(maxes):
        return ' class="yield-3"'
    if avgs and current >= max(avgs):
        return ' class="yield-2"'
    if avgs and current >= min(avgs):
        return ' class="yield-1"'
    return ' class="yield-0"'


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

    timestamp = rows[-1].get("timestamp", rows[-1]["date"])

    table_lines = []
    for r in rows:
        table_lines.append(
            f"<tr{_row_class(r)}>"
            f"<td><a href=\"https://scouter.monex.co.jp/report/index/{r.get('code', '')}\" target=\"_blank\">{_cell(r.get('code', ''))}</a></td>"
            f"<td>{_cell(r.get('name', ''))}</td>"
            f"<td>{_cell(r.get('sector', ''))}</td>"
            f"<td>{_cell(r.get('price', ''))}</td>"
            f"<td>{_cell(r.get('per', ''))}</td>"
            f"<td>{_cell(r.get('pbr', ''))}</td>"
            f"<td>{_cell(r.get('dividend_yield_forecast', ''))}</td>"
            f"{_change_cell(r.get('yield_1d_change', ''))}"
            f"{_change_cell(r.get('yield_1w_change', ''))}"
            f"<td>{_cell(r.get('yield_1y_min', ''))}</td>"
            f"<td>{_cell(r.get('yield_1y_avg', ''))}</td>"
            f"<td>{_cell(r.get('yield_1y_max', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_min', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_avg', ''))}</td>"
            f"<td>{_cell(r.get('yield_2y_max', ''))}</td>"
            f"</tr>"
        )

    html = HTML_TEMPLATE.format(
        updated=timestamp,
        rows="\n".join(table_lines),
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {HTML_PATH}")


if __name__ == "__main__":
    generate()
