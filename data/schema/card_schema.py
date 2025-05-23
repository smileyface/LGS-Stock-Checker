from typing import Optional

from pydantic import BaseModel  # pip install pydantic


class CardSpecificationSchema(BaseModel):
    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    finish: Optional[str] = None
