# ==========================================================
# Utility: Get Client IP Address
# ==========================================================

def get_client_ip(request):
    """
    Extracts the client IP address from the request object.
    Steps:
    1. Check for 'HTTP_X_FORWARDED_FOR' header (used when behind proxies/load balancers).
    2. If present, take the first IP in the list.
    3. If not present, fall back to 'REMOTE_ADDR'.
    4. Return the resolved IP address as a string.
    """

    # Step 1: Check forwarded header (proxy-aware)
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    # Step 2: If header exists, take first IP
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        # Step 3: Fallback to REMOTE_ADDR
        ip = request.META.get("REMOTE_ADDR")

    # Step 4: Return IP
    return ip
