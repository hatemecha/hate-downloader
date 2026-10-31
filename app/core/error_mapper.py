class UserError:
    def __init__(self, message: str, detail: str = "", action: str = "") -> None:
        self.message = message
        self.detail = detail
        self.action = action


ERROR_MAP: dict[str, dict[str, str]] = {
    "ffmpeg_not_found": {
        "message": "FFmpeg not found.",
        "detail": "Hate Downloader can analyze links, but needs FFmpeg "
        "to merge audio/video or convert files.",
        "action": "Install FFmpeg in the Dependencies window.",
    },
    "ffprobe_not_found": {
        "message": "FFprobe not found.",
        "detail": "FFprobe is needed to inspect media files.",
        "action": "Install FFmpeg in the Dependencies window.",
    },
    "video_unavailable": {
        "message": "This video is unavailable.",
        "detail": "The video may have been removed or is restricted.",
        "action": "",
    },
    "private_video": {
        "message": "This video is private.",
        "detail": "Sign in may be required to access this content.",
        "action": "Use cookies from your browser in Settings.",
    },
    "login_required": {
        "message": "Login required.",
        "detail": "This content needs authentication.",
        "action": "Use cookies from your browser in Settings.",
    },
    "drm_protected": {
        "message": "DRM-protected content.",
        "detail": "This content is protected and cannot be downloaded.",
        "action": "",
    },
    "unsupported": {
        "message": "Unsupported URL.",
        "detail": "This URL is not supported by yt-dlp.",
        "action": "Try Scan page for media on a page with a direct file link.",
    },
    "network_error": {
        "message": "Network error.",
        "detail": "Check your internet connection and try again.",
        "action": "",
    },
    "timeout": {
        "message": "Connection timed out.",
        "detail": "The server took too long to respond.",
        "action": "",
    },
    "format_unavailable": {
        "message": "No available formats found for this media.",
        "detail": "The selected format is not available for this media.",
        "action": "",
    },
    "postprocessing_failed": {
        "message": "Post-processing failed.",
        "detail": "FFmpeg may be missing or corrupted.",
        "action": "Check FFmpeg in the Dependencies window.",
    },
    "extractor_error": {
        "message": "Could not extract media information.",
        "detail": "The extractor encountered an error processing this URL.",
        "action": "",
    },
}


def get_user_error(error_type: str, detail: str = "") -> UserError:
    info = ERROR_MAP.get(
        error_type,
        {
            "message": "An unexpected error occurred.",
            "detail": detail,
            "action": "",
        },
    )
    return UserError(
        message=info["message"],
        detail=detail or info["detail"],
        action=info["action"],
    )


def classify_error(error: Exception) -> UserError:
    msg = str(error)
    lowered = msg.lower()

    if "ffmpeg" in lowered and "not found" in lowered:
        return get_user_error("ffmpeg_not_found", msg)
    if "ffprobe" in lowered:
        return get_user_error("ffprobe_not_found", msg)
    if "video unavailable" in lowered:
        return get_user_error("video_unavailable", msg)
    if "private video" in lowered or "this video is private" in lowered:
        return get_user_error("private_video", msg)
    if "sign in" in lowered or "login" in lowered:
        return get_user_error("login_required", msg)
    if "drm" in lowered:
        return get_user_error("drm_protected", msg)
    if "unsupported" in lowered or "not supported" in lowered:
        return get_user_error("unsupported", msg)
    if "timeout" in lowered:
        return get_user_error("timeout", msg)
    if "http error" in lowered:
        return UserError(
            message="The server refused or could not complete the request.",
            detail=msg,
            action="Try again later. If it persists, update the app or yt-dlp.",
        )
    if "postprocessing" in lowered:
        return get_user_error("postprocessing_failed", msg)
    if "no video" in lowered or "no format" in lowered:
        return get_user_error("format_unavailable", msg)
    if "extractor" in lowered:
        return get_user_error("extractor_error", msg)

    return UserError(
        message="An unexpected error occurred.",
        detail=msg,
        action="",
    )
