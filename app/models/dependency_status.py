from pydantic import BaseModel

from app import __version__


class DependencyInfo(BaseModel):
    name: str
    installed: bool
    version: str = ""
    path: str = ""
    optional: bool = False
    status_message: str = ""
    download_url: str = ""
    actionable: bool = False


class SystemStatus(BaseModel):
    dependencies: list[DependencyInfo] = []
    app_version: str = __version__
    python_version: str = ""
    platform: str = ""
    download_folder_writable: bool = False
    download_folder: str = ""
    all_ok: bool = False
    can_download: bool = False
    can_convert: bool = False
    can_accelerate: bool = False
