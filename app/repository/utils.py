from botocore.exceptions import ClientError
from types_aiobotocore_dynamodb.service_resource import Table
from types_aiobotocore_dynamodb.type_defs import QueryInputTableQueryTypeDef

from app.errors.app_exception import AppException
from app.errors.codes import AppErr


def build_update_expression(updates: dict) -> tuple[str, dict, dict]:
    """
    Builds a update expression for the a dictionary data input

    returns: tuple( update_expression, expression_names_dict, expression_values_dict )
    """
    expr: list[str] = []
    names = {}
    values = {}

    for key, val in updates.items():
        name_key = f"#{key}"
        value_key = f":{key}"
        expr.append(f"{name_key}={value_key}")
        names[name_key] = key
        values[value_key] = val

    return (
        "SET " + ", ".join(expr),
        names,
        values
    )


async def offset_query(
        table: Table,
        query_input: QueryInputTableQueryTypeDef,
        page: int,
        limit: int,
) -> QueryInputTableQueryTypeDef | None:
    if page <= 0:
        return query_input

    prev_select = query_input.get("Select", None)
    prev_projection = query_input.get("ProjectionExpression", None)
    prev_limit = query_input.get("Limit", None)

    query_input["Select"] = "SPECIFIC_ATTRIBUTES"
    query_input["ProjectionExpression"] = "PK, SK"

    offset = limit * page
    last_evaluated_key = None

    query_input["Limit"] = limit
    while offset > 0:
        if last_evaluated_key is not None:
            query_input["ExclusiveStartKey"] = last_evaluated_key
        result = await table.query(**query_input)
        if "LastEvaluatedKey" not in result or "Items" not in result:
            return None
        last_evaluated_key = result["LastEvaluatedKey"]
        offset -= limit
        if last_evaluated_key is None:
            break

    if last_evaluated_key is None:
        return None

    del query_input["Select"]
    del query_input["ProjectionExpression"]
    del query_input["Limit"]
    if prev_select is not None:
        query_input["Select"] = prev_select
    if prev_projection is not None:
        query_input["ProjectionExpression"] = prev_projection
    if prev_limit is not None:
        query_input["Limit"] = prev_limit
    query_input["ExclusiveStartKey"] = last_evaluated_key
    return query_input


def handle_dynamo_error(err: ClientError, msg: str = "Operation failed") -> AppException:
    code = err.response.get("Error", {}).get("Code", "")
    if code == "ProvisionedThroughputExceededException":
        return AppException(AppErr.THROTTLE)
    return AppException(AppErr.INTERNAL, msg, cause=err)
