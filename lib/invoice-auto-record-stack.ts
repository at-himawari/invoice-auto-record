import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3n from "aws-cdk-lib/aws-s3-notifications";

export class InvoiceAutoRecordStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // 1. 既存のS3バケットを参照する
    // 'himawari-accounting' という名前のバケットを取得します
    const bucket = s3.Bucket.fromBucketName(
      this,
      "ImportedBucket",
      "himawari-accounting" // 対象のバケット名を指定
    );

    // 2. Lambda関数の作成 (変更なし)
    const ledgerFunction = new lambda.Function(this, "LedgerUpdater", {
      runtime: lambda.Runtime.PYTHON_3_13,
      handler: "index.lambda_handler",
      code: lambda.Code.fromAsset("lambda"),
      environment: {
        // 必要に応じて環境変数を追加
      },
    });

    // 3. 権限設定 (Lambdaがこの既存バケットを読み書きできるようにする)
    bucket.grantReadWrite(ledgerFunction);

    // 4. トリガー設定 (ファイルが置かれたらLambdaを起動)
    // 既存バケットに対してイベント通知を追加します
    bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(ledgerFunction),
      { suffix: ".pdf" }
    );
  }
}
