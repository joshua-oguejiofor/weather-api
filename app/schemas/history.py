from .base import LoweredStripedSchema
from datetime import datetime


class SearchHistoryResponse(LoweredStripedSchema):
    id: int
    query: str
    query_type: str
    result_city: str | None= None
    result_country: str | None= None
    searched_at: datetime
