# monex-dividend-collector

[マネックス銘柄スカウターライト](https://scouter.monex.co.jp)から予想配当利回り統計を定期収集し、GitHub Pages で公開するツール。

**Pages:** https://yoohya.github.io/monex-dividend-collector/

**対象銘柄:** [`stocks.json`](stocks.json)

## ローカル実行

```bash
pip install -r requirements.txt
playwright install chromium
python scraper.py
python generate_html.py
```
