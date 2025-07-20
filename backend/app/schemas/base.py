from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True
