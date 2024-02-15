import boto3
import json

DYNAMO_DB_TABLE = "my-workloads"

def get_sleep_value(env_name):
    if env_name is not None:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(DYNAMO_DB_TABLE)
        response = table.get_item(Key={"env-name": env_name})
        item = response.get("Item")
        print(item)
        if item is not None:
            sleep_value = item.get("sleep")
            if sleep_value is not None:
                return sleep_value
        return False
    else:
        # return all env-name and sleep keys from the dynamodb table
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(DYNAMO_DB_TABLE)
        response = table.scan()
        items = response["Items"]
        return items


def set_sleep(sleep, workload):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(DYNAMO_DB_TABLE)

    response = table.scan()
    items = response["Items"]

    for item in items:
        if workload is None or item["env-name"] == workload:
            response = table.update_item(
                Key={"env-name": item["env-name"]},
                UpdateExpression="set sleep = :r",
                ExpressionAttributeValues={
                    ":r": sleep,
                },
                ReturnValues="UPDATED_NEW",
            )
            print(f"Updated sleep value for {item['env-name']}")


def lambda_handler(event, context):
    print("Event Is: " + str(event))
    if event.get("httpMethod") == "GET":
        # Retrieve query parameters from the event
        query_params = event.get("queryStringParameters")

        if event.get("resource") == "/sleep":
            workload = query_params.get("workload", "Unknown")
            replicas = query_params.get("replicas", 0)

            res = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"replicaCount": (0 if get_sleep_value(workload) else replicas)}
                ),
            }
            print(res)
            return res

        elif event.get("resource") == "/sleep/status":
            res = {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    get_sleep_value(query_params.get("workload") if query_params is not None else None)
                ),
            }
            return res

    elif event.get("httpMethod") == "POST":
        if event.get("resource") == "/sleep":
            try:
                json_body = json.loads(event.get("body"))
            except:
                json_body = event.get("body")
            sleep = json_body.get("sleep")
            workload = json_body.get("workload")
            set_sleep(sleep, workload)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"success": True}),
            }