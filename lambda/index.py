# lambda/index.py
import json
import os
import requests
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError
import logging


# Lambda コンテキストからリージョンを抽出する関数
 @@ -20,121 +27,269 @@ def extract_region_from_arn(arn):
# モデルID
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")

def lambda_handler(event, context):
    try:
        logging.info("Received event: %s", event)

        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        logging.info("Processing message: %s", message)


        # 会話履歴を使用
        messages = conversation_history.copy()

        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })

        NGROK_API_URL = os.environ.get(
            "NGROK_API_URL",
            "https://8a82-34-16-251-35.ngrok-free.app"
        )
        payload = {
            "message": message,
            "conversationHistory": conversation_history
        }
        logging.info("Calling external API %s with payload %s", NGROK_API_URL, payload)
        api_resp = requests.post(NGROK_API_URL, json=payload, timeout=30)
        api_resp.raise_for_status()
        response_body = api_resp.json()
        logging.info("External API response: %s", response_body)

        # 応答の検証
        if not response_body.get("response"):
            raise Exception("No response field in external API result")
        assistant_response = response_body["response"]

        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }

    except Exception as error:
        print("Error:", str(error))

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
