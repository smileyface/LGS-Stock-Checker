from pydantic import BaseModel, ConfigDict


class StoreSchema(BaseModel):
    id: int
    name: str
    slug: str
    homepage: str
    search_url: str
    fetch_strategy: str

    model_config = ConfigDict(from_attributes=True)
