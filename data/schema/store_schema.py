from pydantic import BaseModel


class StoreSchema(BaseModel):
    id: int
    name: str
    slug: str
    homepage: str
    search_url: str
    fetch_strategy: str

    class Config:
        from_attributes = True