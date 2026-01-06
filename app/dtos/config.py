from pydantic import ConfigDict, Field


def FieldAlias(alias: str, **kwargs):
    return Field(validation_alias=alias,
                 **kwargs)


def default_model_config(**kwargs):
    """
    - by default validates and serializes by alias
    - use enum values
    - ignores extra values
    """
    return ConfigDict(validate_by_name=False,
                      validate_by_alias=True,
                      serialize_by_alias=True,
                      use_enum_values=True,
                      extra="ignore",
                      **kwargs)
