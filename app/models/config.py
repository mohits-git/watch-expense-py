from pydantic import ConfigDict, Field


def FieldAlias(alias: str, **kwargs):
    return Field(validation_alias=alias,
                 serialization_alias=alias,
                 **kwargs)


def default_model_config(**kwargs):
    return ConfigDict(validate_by_name=True,
                      validate_by_alias=False,
                      serialize_by_alias=False,
                      use_enum_values=True,
                      **kwargs)
