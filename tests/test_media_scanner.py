import httpx

from app.core.media_scanner import DirectMediaScanner


def test_scan_resolves_redirected_page_and_media_query_strings():
    scanner = DirectMediaScanner()

    def respond(request):
        if request.url.path == "/original":
            return httpx.Response(302, headers={"Location": "/redirected/page"})
        return httpx.Response(
            200, text='<a href="clip.mp4?token=123">Clip</a><video src="movie.webm"></video>'
        )

    scanner._client = httpx.Client(
        transport=httpx.MockTransport(respond), follow_redirects=True
    )
    try:
        results = scanner.scan("https://example.com/original")
    finally:
        scanner._client.close()
    assert {result.url for result in results} == {
        "https://example.com/redirected/clip.mp4?token=123",
        "https://example.com/redirected/movie.webm",
    }
