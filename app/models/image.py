from pydantic import BaseModel, ConfigDict, Field


class ImageMetadata(BaseModel):
    user_id: str = Field(alias="UserID")

    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=False,
        use_enum_values=True
    )
