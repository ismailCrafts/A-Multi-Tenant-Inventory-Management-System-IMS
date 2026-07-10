from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import json, os

# dashboard_app/views.py
def error_lookup(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "You do not have permission to view error diagnostics.")
        return redirect("login")

    cid = request.GET.get("cid")
    path = os.path.join(settings.BASE_DIR, "error_logs.jsonl")
    record = None

    if cid and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if r.get("cid") == cid:
                        # normalize headers keys for template safety
                        headers = r.get("headers", {})
                        safe_headers = {k.replace("-", "_"): v for k, v in headers.items()}
                        r["headers"] = safe_headers
                        record = r
                        break
                except:
                    continue

    return render(request, "admin/error_lookup.html", {"cid": cid, "record": record})
