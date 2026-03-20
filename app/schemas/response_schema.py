from pydantic import BaseModel


class ResponseMessage(BaseModel):
    #Base schema for standard response messages, can be extended for more specific responses.
    
    success: bool
    message: str