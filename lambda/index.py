import boto3
import csv
import os
import urllib.parse
from datetime import datetime
from io import StringIO

s3 = boto3.client('s3')
# ファイル名を指定のものに変更
LEDGER_FILENAME = '取引情報訂正・削除申請書.csv'
# 処理担当者名（環境変数から取得、なければデフォルト値）
PROCESSOR_NAME = os.environ.get('PROCESSOR_NAME', '自動処理システム')

def parse_filename(filename):
    """ファイル名から情報を抽出する"""
    name_body = os.path.splitext(filename)[0]
    parts = name_body.split('_')
    length = len(parts)
    
    data = {'date': '', 'vendor': '', 'amount': 0, 'memo': '', 'file': filename}

    try:
        if length == 4: # 20241031_Amazon_1000_Memo
            data.update({'date': parts[0], 'vendor': parts[1], 'amount': int(parts[2]), 'memo': parts[3]})
        elif length == 3: # 20241031_Amazon_1000
            data.update({'date': parts[0], 'vendor': parts[1], 'amount': int(parts[2])})
        elif length == 2:
            # ▼▼▼ 修正箇所: 8桁ではなく6桁(YYYYMM)を判定するように変更 ▼▼▼
            if len(parts[0]) == 6: # 202410_Visa
                # ソート用に '01' を足して YYYYMM01 (8桁) に揃える
                data.update({'date': parts[0] + '01', 'vendor': parts[1], 'amount': 0, 'memo': '要金額確認'})
            # ▲▲▲ 修正箇所ここまで ▲▲▲
            
            elif len(parts[0]) == 4: # 2024_Visa
                data.update({'date': parts[0] + "0101", 'vendor': parts[1], 'amount': 0, 'memo': '年間データ'})
        else:
            data['memo'] = '形式不明'
    except Exception:
        data['memo'] = 'パースエラー'
        
    return data

def lambda_handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    # 自分自身の更新通知は無視
    if key == LEDGER_FILENAME:
        print("Ledger file update ignored.")
        return

    print(f"Processing file: {key}")

    # 1. S3から現在のCSVを取得（なければ新規作成）
    existing_data = []
    try:
        response = s3.get_object(Bucket=bucket_name, Key=LEDGER_FILENAME)
        # Excel用に utf-8-sig (BOM付き) で読み込む
        content = response['Body'].read().decode('utf-8-sig')
        reader = csv.DictReader(StringIO(content))
        existing_data = list(reader)
    except s3.exceptions.NoSuchKey:
        print("Creating new ledger file.")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        existing_data = []

    # 2. ファイル情報を解析
    filename_only = os.path.basename(key)
    parsed = parse_filename(filename_only)
    
    # 3. 指定された8項目へのデータマッピングを作成
    now_str = datetime.now().strftime('%Y/%m/%d')
    
    new_entry = {
        '申請日': now_str,
        '取引伝票番号': parsed['file'],
        '取引件名': f"{parsed['memo']} (金額:{parsed['amount']}円)",
        '取引先名': parsed['vendor'],
        '訂正・削除日付': now_str,
        '訂正・削除内容': '電子取引データの新規保存または更新',
        '訂正・削除理由': '正規業務フローに基づくアップロード',
        '処理担当者名': PROCESSOR_NAME
    }

    # 4. データを追加
    existing_data.append(new_entry)

    # 5. CSVを書き込み
    csv_buffer = StringIO()
    fieldnames = [
        '申請日', '取引伝票番号', '取引件名', '取引先名', 
        '訂正・削除日付', '訂正・削除内容', '訂正・削除理由', '処理担当者名'
    ]
    
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(existing_data)

    # utf-8-sig (BOM付き) でエンコードして保存
    s3.put_object(
        Bucket=bucket_name, 
        Key=LEDGER_FILENAME, 
        Body=csv_buffer.getvalue().encode('utf-8-sig')
    )
    
    print(f"Application form updated with {filename_only}")