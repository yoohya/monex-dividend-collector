# monex-dividend-collector

マネックス銘柄スカウターライト（認証不要）から予想配当利回り統計を定期収集し、GitHub Pages で公開するツール。

**Pages:** https://yoohya.github.io/monex-dividend-collector/

## 取得項目

- 予想配当利回り（現在値）
- 株価
- 予想配当利回り 1年統計: 最大値・最小値・平均値
- 予想配当利回り 2年統計: 最大値・最小値・平均値

## 監視対象銘柄

| コード | 銘柄名 | セクター |
|--------|--------|----------|
| 7203 | トヨタ自動車 | 輸送用機器 |
| 6758 | ソニーグループ | 電気機器 |
| 8306 | 三菱UFJフィナンシャル・グループ | 銀行業 |
| 8058 | 三菱商事 | 卸売業 |
| 8031 | 三井物産 | 卸売業 |
| 8001 | 伊藤忠商事 | 卸売業 |
| 8053 | 住友商事 | 卸売業 |
| 8002 | 丸紅 | 卸売業 |
| 8316 | 三井住友フィナンシャルグループ | 銀行業 |
| 8411 | みずほフィナンシャルグループ | 銀行業 |
| 8766 | 東京海上ホールディングス | 保険業 |
| 8725 | MS&ADインシュアランスグループホールディングス | 保険業 |
| 8630 | SOMPOホールディングス | 保険業 |
| 7011 | 三菱重工業 | 機械 |
| 7012 | 川崎重工業 | 輸送用機器 |
| 7013 | IHI | 機械 |

銘柄の追加・変更は `stocks.json` を編集してください。

## 仕組み

1. **scraper.py** - Playwright で[銘柄スカウターライト](https://scouter.monex.co.jp)の Highcharts チャートから配当利回りデータを取得
2. **generate_html.py** - CSV データからソート可能な HTML テーブルを生成
3. **GitHub Actions** - 平日 JST 16:30 に自動実行し、結果を GitHub Pages にデプロイ

## 構成

```
├── scraper.py                       # スクレイパー本体
├── generate_html.py                 # HTML生成
├── stocks.json                      # 監視対象銘柄リスト
├── requirements.txt                 # Python依存パッケージ
└── .github/workflows/
    └── collect.yml                  # データ収集 & Pagesデプロイ
```

`output/` はワークフロー内で動的に生成され、GitHub Pages の artifact として直接デプロイされます。

## ローカル実行

```bash
pip install -r requirements.txt
playwright install chromium
python scraper.py
python generate_html.py
```

## 注意

- Highcharts チャートのコンテナインデックス（Container 3 = 予想配当利回り）がサイト改修で変わる可能性あり
- `.summary` セクションの DOM 構造に依存するため、サイト改修時はセレクタの更新が必要
- サーバー負荷軽減のため銘柄間に1秒の sleep を入れている
- 無料版では1年・2年のみ対応（3年・全期間は選択不可）
