from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import QueryInputTableQueryTypeDef


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


def offset_query(
        table: Table,
        query_input: QueryInputTableQueryTypeDef,
        page: int,
        limit: int,
) -> QueryInputTableQueryTypeDef | None:
    if page <= 0:
        return query_input

    prev_select = query_input["Select"] if "Select" in query_input else None
    prev_projection = query_input["ProjectionExpression"] if "ProjectionExpression" in query_input else None

    query_input["Select"] = "SPECIFIC_ATTRIBUTES"
    query_input["ProjectionExpression"] = "PK, SK"

    offset = limit * page
    last_evaluated_key = None

    while offset > 0:
        if last_evaluated_key is not None:
            query_input["ExclusiveStartKey"] = last_evaluated_key
        query_input["Limit"] = limit
        result = table.query(**query_input)
        if "LastEvaluatedKey" not in result or "Items" not in result:
            return None
        last_evaluated_key = result["LastEvaluatedKey"]
        offset -= len(result["Items"])
        if last_evaluated_key is None:
            break

    if last_evaluated_key is None:
        return None

    if prev_select is not None:
        query_input["Select"] = prev_select
    if prev_projection is not None:
        query_input["ProjectionExpression"] = prev_projection
    query_input["ExclusiveStartKey"] = last_evaluated_key
    return query_input
