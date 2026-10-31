from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    duration: int = 0
    uploader: str = ""
    thumbnail: str = ""
    source: str = ""
    description: str = ""
    identifier: str = ""
    extractor: str = ""
    format: str = ""
    size: str = ""
