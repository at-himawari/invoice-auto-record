import boto3
import csv
import os
import urllib.parse
from datetime import datetime
from io import StringIO

s3 = boto3.client('s3')
LEDGER_FILENAME = '取引情報訂正・削除申請書.csv'

def parse_filename(filename):
    """ファイル名から日付・取引先・金額・メモを抽出する"""
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
            if len(parts[0]) == 8: # 20241031_Visa
                data.update({'date': parts[0], 'vendor': parts[1], 'amount': 0, 'memo': '要金額確認'})
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

    # 【重要】自分自身(ledger.csv)の更新通知は無視する（無限ループ防止）
    if key == LEDGER_FILENAME:
        print("Ledger file update ignored.")
        return

    print(f"Processing file: {key}")

    # 1. S3から現在のledger.csvを取得（なければ新規作成）
    existing_data = []
    try:
        response = s3.get_object(Bucket=bucket_name, Key=LEDGER_FILENAME)
        content = response['Body'].read().decode('utf-8')
        reader = csv.DictReader(StringIO(content))
        existing_data = list(reader)
    except s3.exceptions.NoSuchKey:
        print("Creating new ledger file.")

    # 2. アップロードされたファイル情報を解析
    # フォルダ(Prefix)が含まれる場合はファイル名だけ取り出す
    filename_only = os.path.basename(key)
    new_entry = parse_filename(filename_only)
    
    # フルパス（S3キー）も保存しておく（リンク用）
    new_entry['file_path'] = key 

    # 3. データを追加
    existing_data.append(new_entry)
    
    # 日付順にソート（オプション）
    existing_data.sort(key=lambda x: x['date'])

    # 4. CSVを書き込み
    csv_buffer = StringIO()
    fieldnames = ['date', 'vendor', 'amount', 'memo', 'file', 'file_path']
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(existing_data)

    # 5. S3に保存（これがトリガーにならないように除外設定が必要だが、今回はコード冒頭でガードしている）
    s3.put_object(Bucket=bucket_name, Key=LEDGER_FILENAME, Body=csv_buffer.getvalue())
    print(f"Ledger updated with {filename_only}")