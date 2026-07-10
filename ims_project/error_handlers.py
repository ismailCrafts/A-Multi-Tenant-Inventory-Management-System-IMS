import logging
import uuid
import traceback
import json
import os
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger(__name__)

# Path to store structured error records (JSON lines)
ERROR_LOG_PATH = os.path.join(settings.BASE_DIR, "error_logs.jsonl")

def _cid():
    """Generate a short correlation id for tracking errors."""
    return uuid.uuid4().hex[:8]

def _log_error(cid, request, exc_info=None, extra=None):
    """Persist error details to a JSONL file for admin lookup."""
    try:
        tb = "".join(traceback.format_exception(*exc_info)) if exc_info else None
        record = {
            "cid": cid,
            "path": request.path,
            "method": request.method,
            "user": getattr(request.user, "username", None),
            "ip": request.META.get("REMOTE_ADDR"),
            "headers": {
                "User-Agent": request.META.get("HTTP_USER_AGENT"),
                "Referer": request.META.get("HTTP_REFERER"),
            },
            "traceback": tb,
            "extra": extra or {},
        }
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        logger.exception("Failed to log error cid=%s", cid)

# ---------------- 500 Internal Server Error ----------------
def handler500(request):
    import sys
    cid = _cid()
    logger.exception("500 error cid=%s path=%s", cid, request.path)
    _log_error(cid, request, exc_info=sys.exc_info())
    return render(request, "errors/500.html", {"cid": cid}, status=500)

# ---------------- 404 Not Found ----------------
def handler404(request, exception):
    cid = _cid()
    logger.warning("404 error cid=%s path=%s", cid, request.path)
    _log_error(cid, request, extra={"reason": "404"})
    return render(request, "errors/404.html", {"cid": cid, "path": request.path}, status=404)

# ---------------- 403 Forbidden ----------------
def handler403(request, exception):
    cid = _cid()
    logger.warning("403 error cid=%s path=%s", cid, request.path)
    _log_error(cid, request, extra={"reason": "403"})
    return render(request, "errors/403.html", {"cid": cid}, status=403)
