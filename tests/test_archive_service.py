import httpx

from app.core.archive_service import InternetArchiveProvider


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "response": {
                "docs": [
                    {
                        "identifier": "foo-id",
                        "title": ["Foo Title"],
                        "creator": "Someone",
                        "description": ["A clip"],
                    }
                ]
            }
        }


class _FakeClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, *args) -> bool:
        return False

    def get(self, url, params=None, headers=None) -> _FakeResponse:
        assert "advancedsearch.php" in url
        return _FakeResponse()


def test_archive_search_maps_json(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    results = InternetArchiveProvider().search("foo", limit=5)
    assert len(results) == 1
    assert results[0].title == "Foo Title"
    assert results[0].url == "https://archive.org/details/foo-id"
    assert results[0].source == "Internet Archive"


def test_archive_search_blank_query() -> None:
    assert InternetArchiveProvider().search("   ") == []
