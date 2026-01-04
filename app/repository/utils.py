from boto3.dynamodb.types import TypeSerializer, TypeDeserializer


def dynamo_to_python(dynamo_object: dict) -> dict:
    deserializer = TypeDeserializer()
    return {
        k: deserializer.deserialize(v)
        for k, v in dynamo_object.items()
    }


def python_to_dynamo(python_object: dict) -> dict:
    serializer = TypeSerializer()
    return {
        k: serializer.serialize(v)
        for k, v in python_object.items()
    }


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
