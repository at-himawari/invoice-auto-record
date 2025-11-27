# Invoice Auto Record

請求書 PDF ファイルが S3 バケットにアップロードされると、自動的に取引情報を記録するシステムです。

## 概要

このプロジェクトは、AWS CDK を使用して構築された請求書自動記録システムです。S3 バケットに PDF ファイルがアップロードされると、Lambda 関数が自動的にトリガーされ、ファイル名から取引情報を抽出して「取引情報訂正・削除申請書.csv」に記録します。

国税庁の以下のファイルに準じたフォーマットをフォルダ直下に置くことを推奨します。
[電子取引データの訂正及び削除の防止に関する事務処理規程（個人事業者の例）（Word/18KB）](https://www.nta.go.jp/law/joho-zeikaishaku/sonota/jirei/word/0021006-031_e.docx)

## 機能

- S3 バケットへの PDF ファイルアップロードを自動検知
- ファイル名から取引情報（日付、取引先、金額、メモ）を自動抽出
- CSV 形式で取引情報を記録・更新
- Excel 互換の BOM 付き UTF-8 エンコーディング

## ファイル名の形式

以下の形式のファイル名に対応しています：

- `YYYYMMDD_取引先_金額_メモ.pdf` - 例: `20241031_Amazon_1000_備品購入.pdf`
- `YYYYMMDD_取引先_金額.pdf` - 例: `20241031_Amazon_1000.pdf`
- `YYYYMM_取引先.pdf` - 例: `202410_Visa.pdf` (金額確認が必要な場合)
- `YYYY_取引先.pdf` - 例: `2024_Visa.pdf` (年間データ)

## 前提条件

- Node.js (v14 以上)
- AWS CLI 設定済み
- AWS CDK CLI (`npm install -g aws-cdk`)
- Python 3.13 以上

## セットアップ

1. 依存関係のインストール:

```bash
npm install
```

2. TypeScript のビルド:

```bash
npm run build
```

3. CDK のブートストラップ（初回のみ）:

```bash
cdk bootstrap
```

## デプロイ

```bash
cdk deploy
```

## 環境変数

Lambda 関数で以下の環境変数を設定できます：

- `PROCESSOR_NAME` - 処理担当者名（デフォルト: "自動処理システム"）

## 出力 CSV 形式

以下の項目を含む CSV ファイルが生成されます：

- 申請日
- 取引伝票番号
- 取引件名
- 取引先名
- 訂正・削除日付
- 訂正・削除内容
- 訂正・削除理由
- 処理担当者名

## 開発

### テストの実行

```bash
npm test
```

### ウォッチモード

```bash
npm run watch
```

## 使用技術

- AWS CDK
- AWS Lambda (Python 3.13)
- AWS S3
- TypeScript
- Python

## ライセンス

MIT
