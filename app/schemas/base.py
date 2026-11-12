from pydantic import BaseModel, field_validator


class StripedSchema(BaseModel):
   
    @field_validator("*", mode= "before")
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value
    
    
    model_config = {
        "extra": "forbid", 
        "populate_by_name": True, 
        "from_attributes": True
        }
    
    


class LoweredStripedSchema(BaseModel):
    
    @field_validator("*", mode= "before")
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value
    
    
    model_config = {
        "extra": "forbid", 
        "populate_by_name": True, 
        "from_attributes": True
        }