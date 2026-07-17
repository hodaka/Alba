# Alba — 設定資料集

TRPG／ゲーム制作のための設定資料集リポジトリ。

## 構成
- `stories/` … 一次ソース（本文）。正史の原本。
- `characters/` … 二次資料（キャラ設定）。本文から導く。
- `world/` … 世界観・用語・命名規則・歴史。
- `assets/` … 立ち絵・画像・プロンプト等。
- `canon-notes.md` … 未確定・保留事項。

## 原則
本文（stories）が正史の唯一の正。二次資料が本文と食い違う場合は本文を優先する。

## リリース（資料の一括ダウンロード）
タグを push するか、手動トリガーで、資料一式を zip に固めた Release が作られる。
詳細は下記「リリース手順」参照。

## リリース手順

資料を一括ダウンロードしたくなったら、次のどちらか：

- **タグ方式**：
  ```
  git tag v1.0.0
  git push origin v1.0.0
  ```
  → Actions が走り、`Alba-v1.0.0.zip` が付いた Release ができる。

- **手動方式**：GitHub の Actions タブ →「Release (bundle assets to zip)」→ Run workflow。
  タグ名を入れれば任意名で、空なら日付スナップショットで zip が作られる。

ダウンロードは Release ページの Assets からその zip を落とすだけ。
