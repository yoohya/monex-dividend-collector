# monex-dividend-collector

マネックス銘柄スカウターライト（認証不要）から予想配当利回り統計を定期収集するツール。

## 構成

- `scraper.py` - スクレイパー本体。Playwright で `scouter.monex.co.jp` のチャートデータを取得
- `generate_html.py` - CSVデータからHTML生成
- `stocks.json` - 監視対象銘柄リスト（銘柄コードと名前）
- `.github/workflows/collect.yml` - GitHub Actions定期実行（平日 JST 16:30）& Pagesデプロイ
- `output/` はワークフロー内で動的生成（Git管理外）

## データソース

銘柄スカウターライト: `https://scouter.monex.co.jp/report/index/{銘柄コード}`

Highcharts チャート（jQuery経由）から配当利回り統計を取得。Playwright が必要。

## 取得項目

- 予想配当利回り（`.summary` セクションから取得）
- 予想配当利回り 1年統計: 最大値・最小値・平均値（Highcharts Container 3 の plotLines）
- 予想配当利回り 2年統計: 最大値・最小値・平均値（同上、デフォルト表示）

## 開発

```bash
pip install -r requirements.txt
playwright install chromium
python scraper.py
```

## 注意

- Highcharts チャートのコンテナインデックス（Container 3 = 予想配当利回り）がサイト改修で変わる可能性あり
- `.summary` セクションのDOM構造に依存。サイト改修時はセレクタの更新が必要
- サーバー負荷軽減のため銘柄間に1秒のsleepを入れている
- 無料版では1年・2年のみ対応（3年・全期間は選択不可）
