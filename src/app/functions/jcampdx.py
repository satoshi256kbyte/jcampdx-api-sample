"""
JCAMP-DX API Lambda Function
"""

import http
import json
import os

import boto3
import jcamp
import numpy
from aws_lambda_powertools.utilities.typing import LambdaContext

COMMON_HEADER: dict = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "GET",
    "Content-Type": "application/json",
}


def handler(event: dict, context: LambdaContext) -> dict[str, any]:
    """
    ハンドラー関数

    Args:
        event (Dict[str, Any]): Lambda 関数に渡されるイベントデータ。
        context (Any): Lambda 関数の実行コンテキスト。

    Returns:
        Dict[str, Any]: ステータスコードとボディ（ユーザーデータまたはエラーメッセージ）を含むレスポンス。
    """

    request_context: dict = event.get("requestContext", {})
    http_method: str = request_context.get("http", {}).get("method", "")
    http_method = http_method.upper()

    if http_method != "GET":
        return {
            "isBase64Encoded": False,
            "statusCode": http.HTTPStatus.METHOD_NOT_ALLOWED,
            "headers": COMMON_HEADER,
            "body": json.dumps({"message": "Method not allowed"}),
        }

    params: dict = event.get("pathParameters", {}) or {}
    if not params.get("jcampdx_id", ""):

        return {
            "isBase64Encoded": False,
            "statusCode": http.HTTPStatus.BAD_REQUEST,
            "headers": COMMON_HEADER,
            "body": json.dumps({"message": "Bad Reqeust"}),
        }

    jdx_data: str = get_jdx_from_dynamodb(params.get("jcampdx_id", ""))
    jdx_parsed: dict = parse_jdx(jdx_data)
    jdx_json: str = json.dumps(jdx_parsed, default=serialize_ndarray)

    return {
        "isBase64Encoded": False,
        "statusCode": http.HTTPStatus.OK,
        "headers": COMMON_HEADER,
        "body": jdx_json,
    }


def get_jdx_from_dynamodb(id: str) -> str:
    """
    DynamoDBからJDXデータを取得する

    Args:
        id (str): JDXデータのID

    Returns:
        str: JDXデータ
    """
    dynamodb = boto3.client("dynamodb")

    try:
        response = dynamodb.get_item(
            TableName=os.environ.get("TABLE_NAME"), Key={"jdx_id": {"S": id}}
        )
        return response.get("Item").get("jdx_data").get("S")
    except Exception as e:
        print(f"Error fetching JDX data from DynamoDB: {str(e)}")
        raise e


def parse_jdx(jdx_data: str) -> dict:
    """
    JDXファイルの文字列をデータに変換する

    Args:
        jdx_data (str): JDXデータ

    Returns:
        dict: JDXデータを解析したデータ
    """

    try:
        return jcamp.jcamp_read(jdx_data.splitlines())
    except Exception as e:
        print(f"Error parsing JDX data: {str(e)}")
        raise e


def serialize_ndarray(obj: any) -> list:
    """
    NumPy配列をシリアライズ可能な形式に変換する

    Args:
        obj (Any): シリアライズするオブジェクト
    Returns:
        list: シリアライズ可能なオブジェクト
    """

    if isinstance(obj, numpy.ndarray):
        return obj.tolist()
    raise TypeError(f"{obj.__class__.__name__} is not JSON serializable")
