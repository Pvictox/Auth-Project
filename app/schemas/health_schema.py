from pydantic import BaseModel


class HealthStatus(BaseModel):
    id: int
    title: str
    status: str
