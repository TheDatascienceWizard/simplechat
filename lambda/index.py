import json
import os
import urllib.request 
import logging

# 外部APIエンドポイント（ngrokなど）
API_URL = os.environ.get("NGROK_API_URL", "https://8a82-34-16-251-35.ngrok-free.app")

def lambda_handler(event, context):
    try:
        logging.info("Received event: %s", event)

        # ユーザー情報取得（Cognitoなどを使っていれば）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディを読み取り
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        payload = {
            "message": message,
            "conversationHistory": conversation_history
        }
        headers = {
            "Content-Type": "application/json"
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

        # POSTリクエストを送信
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            response_data = json.loads(resp_body)

        # 応答の検証
        if not response_body.get("response"):
            raise Exception("No response field in external API result")
        assistant_response = response_body["response"]

        # アシスタントの応答を会話履歴に追加
        conversation_history.append({
            "role": "user", "content": message
        })
        conversation_history.append({
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
