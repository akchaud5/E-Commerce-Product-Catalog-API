from bson import ObjectId
from typing import Any, Annotated, ClassVar, get_type_hints
import pydantic.json_schema
from pydantic_core import CoreSchema, core_schema
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler, field_serializer, BeforeValidator


def validate_object_id(v: Any) -> ObjectId:
    """Validate that the value is a valid ObjectId."""
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError(f"Invalid ObjectId: {v}")


class PydanticObjectId(ObjectId):
    """Pydantic compatible ObjectId implementation."""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, 
        _source_type: Any, 
        _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Generate schema for ObjectId."""
        return core_schema.union_schema([
            # Handle ObjectId instances
            core_schema.is_instance_schema(ObjectId),
            # Handle strings and validate them as ObjectId format
            core_schema.chain_schema([
                core_schema.string_schema(),
                core_schema.no_info_plain_validator_function(validate_object_id),
            ]),
        ], serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls, 
        _core_schema: CoreSchema, 
        handler: GetJsonSchemaHandler
    ) -> dict[str, Any]:
        """Generate JSON schema for ObjectId."""
        return handler(core_schema.string_schema())


PyObjectId = Annotated[PydanticObjectId, pydantic.json_schema.with_json_schema({"type": "string", "format": "objectid"})]