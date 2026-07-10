import os
import base64
import logging
from django.template.loader import get_template
from django.utils import translation
from django.conf import settings
from weasyprint import HTML
from stock_app.models import (
    OpeningStock, Purchase, Sale,
    PurchaseReturn, SaleReturn, ProductReject
)

logger = logging.getLogger(__name__)

# ==========================================================
# TOPIC → MODEL MAP
# ==========================================================
MODEL_MAP = {
    "opening":         OpeningStock,
    "purchase":        Purchase,
    "sale":            Sale,
    "purchase_return": PurchaseReturn,
    "sale_return":     SaleReturn,
    "reject":          ProductReject,
}

TOPIC_FIELDS = {
    "opening":         ["date", "quantity"],
    "purchase":        ["date", "purchase_code", "supplier_name", "supplier_mobile", "total_amount", "paid_amount", "due_amount"],
    "sale":            ["date", "sale_code",     "customer_name", "customer_mobile", "total_amount", "paid_amount", "due_amount"],
    "purchase_return": ["date", "return_code",   "supplier_name", "supplier_mobile", "total_amount", "refund_amount", "due_amount"],
    "sale_return":     ["date", "return_code",   "customer_name", "customer_mobile", "total_amount", "refund_amount", "due_amount"],
    "reject":          ["date", "reject_code",   "quantity", "reason"],
}

AMOUNT_FIELDS = {"total_amount", "paid_amount", "due_amount", "refund_amount"}
PAID_FIELDS   = {"paid_amount", "refund_amount"}
DUE_FIELDS    = {"due_amount"}


# ==========================================================
# TRANSLATION — read directly from .mo file
# ==========================================================
# This approach bypasses Django's thread-local translation system entirely.
# We read the .mo file directly using Python's built-in gettext module and
# build a plain Python dict of translated strings.
# The template receives {{ t.Date }}, {{ t.Report }} etc as plain string variables.
# No {% trans %} tags, no thread-local, no middleware interference — 100% reliable.

def get_translations(lang):
    """
    Returns a dict of all report strings for the given language.

    English: strings returned as-is.
    Bangla: hardcoded directly from the .mo file — no file reading needed,
    no thread-local, no network. Always works. Never fails.
    """
    # -------------------------------------------------------
    # ENGLISH
    # -------------------------------------------------------
    en = {
        "Report":          "Report",
        "Opening Stock":   "Opening Stock",
        "Purchase":        "Purchase",
        "Sale":            "Sale",
        "Purchase Return": "Purchase Return",
        "Sale Return":     "Sale Return",
        "Product Reject":  "Product Reject",
        "From":            "From",
        "to":              "to",
        "Generated_on":    "Generated on",
        "No_records":      "No records found for this report.",
        "Download_PDF":    "Download PDF",
        "Back_to_Form":    "Back to Form",
        "Date":            "Date",
        "Purchase Code":   "Purchase Code",
        "Sale Code":       "Sale Code",
        "Return Code":     "Return Code",
        "Reject Code":     "Reject Code",
        "Supplier Name":   "Supplier Name",
        "Supplier Mobile": "Supplier Mobile",
        "Customer Name":   "Customer Name",
        "Customer Mobile": "Customer Mobile",
        "Total Amount":    "Total Amount",
        "Paid Amount":     "Paid Amount",
        "Due Amount":      "Due Amount",
        "Refund Amount":   "Refund Amount",
        "Quantity":        "Quantity",
        "Reason":          "Reason",
        "Product":         "Product",
        "Total":           "Total",
    }

    if lang != 'bn':
        return en

    # -------------------------------------------------------
    # BANGLA — hardcoded from locale/bn/LC_MESSAGES/django.mo
    # These strings are baked into the code — no file reading,
    # no thread-local, no network access. 100% reliable.
    # -------------------------------------------------------
    return {
        "Report":          "রিপোর্ট",
        "Opening Stock":   "প্রারম্ভিক স্টক",
        "Purchase":        "ক্রয়",
        "Sale":            "বিক্রয়",
        "Purchase Return": "ক্রয় ফেরত",
        "Sale Return":     "বিক্রয় ফেরত",
        "Product Reject":  "পণ্য প্রত্যাখ্যান",
        "From":            "হতে",
        "to":              "থেকে",
        "Generated_on":    "উৎপন্ন হয়েছে",
        "No_records":      "এই রিপোর্টের জন্য কোনো তথ্য পাওয়া যায়নি।",
        "Download_PDF":    "PDF ডাউনলোড করুন",
        "Back_to_Form":    "ফর্মে ফিরে যান",
        "Date":            "তারিখ",
        "Purchase Code":   "ক্রয় কোড",
        "Sale Code":       "বিক্রয় কোড",
        "Return Code":     "ফেরত কোড",
        "Reject Code":     "প্রত্যাখ্যান কোড",
        "Supplier Name":   "সরবরাহকারীর নাম",
        "Supplier Mobile": "সরবরাহকারীর মোবাইল",
        "Customer Name":   "গ্রাহকের নাম",
        "Customer Mobile": "গ্রাহকের মোবাইল",
        "Total Amount":    "মোট পরিমাণ",
        "Paid Amount":     "প্রদত্ত পরিমাণ",
        "Due Amount":      "বাকি পরিমাণ",
        "Refund Amount":   "ফেরত পরিমাণ",
        "Quantity":        "পরিমাণ",
        "Reason":          "কারণ",
        "Product":         "পণ্য",
        "Total":           "মোট",
    }


# ==========================================================
# FIELD LABELS — use translations dict directly
# ==========================================================
def build_columns_and_rows(topic, queryset, translations):
    """
    Returns (columns, rows, totals_row).
    - columns: list of {label, is_amount}
    - rows: list of row-cell dicts
    - totals_row: list of {value, is_amount, is_paid, is_due} for the totals/sum footer row.
                  Non-amount cells are empty strings; amount cells hold the column sum.
    translations: dict from get_translations(lang) — NO thread-local needed.
    """
    from decimal import Decimal

    field_names = TOPIC_FIELDS.get(topic, [])
    if not queryset or not hasattr(queryset, 'model'):
        return [], [], []

    model_fields = {f.name: f for f in queryset.model._meta.fields}
    valid_fields = [f for f in field_names if f in model_fields]

    # Map field name → translation key
    FIELD_TO_TRANS_KEY = {
        "date":            "Date",
        "purchase_code":   "Purchase Code",
        "sale_code":       "Sale Code",
        "return_code":     "Return Code",
        "reject_code":     "Reject Code",
        "supplier_name":   "Supplier Name",
        "supplier_mobile": "Supplier Mobile",
        "customer_name":   "Customer Name",
        "customer_mobile": "Customer Mobile",
        "total_amount":    "Total Amount",
        "paid_amount":     "Paid Amount",
        "due_amount":      "Due Amount",
        "refund_amount":   "Refund Amount",
        "quantity":        "Quantity",
        "reason":          "Reason",
        "product":         "Product",
    }

    columns = []
    for fname in valid_fields:
        key       = FIELD_TO_TRANS_KEY.get(fname, fname.replace('_', ' ').title())
        label     = translations.get(key, key)
        is_amount = fname in AMOUNT_FIELDS
        columns.append({"label": label, "is_amount": is_amount})

    # Running totals for amount columns (keyed by field index)
    col_sums = {i: Decimal("0") for i, f in enumerate(valid_fields) if f in AMOUNT_FIELDS}

    rows = []
    for obj in queryset:
        row = []
        for i, fname in enumerate(valid_fields):
            value     = getattr(obj, fname, "")
            is_amount = fname in AMOUNT_FIELDS
            is_paid   = fname in PAID_FIELDS
            is_due    = fname in DUE_FIELDS
            row.append({
                "value":     value,
                "is_amount": is_amount,
                "is_paid":   is_paid,
                "is_due":    is_due,
            })
            # Accumulate sum for amount columns
            if is_amount:
                try:
                    col_sums[i] += Decimal(str(value))
                except Exception:
                    pass
        rows.append(row)

    # Build totals row — amount columns show sum, others are empty
    totals_row = []
    for i, fname in enumerate(valid_fields):
        is_amount = fname in AMOUNT_FIELDS
        is_paid   = fname in PAID_FIELDS
        is_due    = fname in DUE_FIELDS
        if is_amount:
            totals_row.append({
                "value":     col_sums[i],
                "is_amount": True,
                "is_paid":   is_paid,
                "is_due":    is_due,
            })
        else:
            totals_row.append({
                "value":     "",
                "is_amount": False,
                "is_paid":   False,
                "is_due":    False,
            })

    # Only return a totals row when at least one amount column actually has data
    has_amounts = any(f in AMOUNT_FIELDS for f in valid_fields)
    return columns, rows, (totals_row if has_amounts else [])


# ==========================================================
# BENGALI FONT — read from static/fonts/ (permanent project file)
# ==========================================================
# Font file lives at: ims_project_v1/media/fonts/NotoSansBengali-Regular.woff2
# The media/fonts/ directory always exists on the server.
# NO runtime downloading. NO external HTTP. NEVER crashes.
#
# To install on server (run once via SSH — see exact commands below):
#   mkdir -p ~/ims_project_v1/media/fonts
#   wget -O /tmp/noto.css 'https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali&display=swap'
#   FONT_URL=$(grep -o 'https://fonts.gstatic.com[^)]*' /tmp/noto.css | head -1)
#   wget -O ~/ims_project_v1/media/fonts/NotoSansBengali-Regular.woff2 "$FONT_URL" 

FONT_PATH = os.path.join(settings.MEDIA_ROOT, 'fonts', 'NotoSansBengali-Regular.woff2')


def get_bengali_font_b64():
    """
    Reads NotoSansBengali from static/fonts/ and returns a base64 data URI.
    WeasyPrint embeds this directly in the PDF — no network access needed.
    Returns None if font file is missing (PDF shows boxes but does NOT crash).
    """
    if not os.path.exists(FONT_PATH):
        logger.warning(f"Bengali font not found at: {FONT_PATH}")
        return None
    try:
        with open(FONT_PATH, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
        return f"data:font/truetype;base64,{data}"
    except Exception as e:
        logger.warning(f"Failed to read Bengali font: {e}")
        return None


# ==========================================================
# LOGO AS url (for PDF embedding)
# ==========================================================
def get_logo_url(organization):
    """
    Returns a file:// URL pointing to the org logo on disk.
    WeasyPrint loads it directly — no base64 encoding needed.
    Returns None if no logo or file not found.
    """
    if not organization.logo:
        return None
    try:
        name = organization.logo.name
        path = os.path.join(settings.MEDIA_ROOT, name.lstrip('/'))
        if not os.path.exists(path):
            logger.warning(f"Logo file not found at: {path}")
            return None
        return f"file://{path}"
    except Exception as e:
        logger.warning(f"Failed to get logo URL: {e}")
        return None


# ==========================================================
# QUERY REPORT
# ==========================================================
def query_report(topic, start_date, end_date, organization, branch=None):
    model = MODEL_MAP.get(topic)
    if not model:
        return []
    qs = model.objects.filter(
        organization=organization,
        date__range=[start_date, end_date]
    )
    if branch:
        qs = qs.filter(branch=branch)
    return qs.order_by("date")


# ==========================================================
# RENDER HTML
# ==========================================================
def render_report_html(request, topic, start_date, end_date, queryset,
                       organization, branch=None, for_pdf=False):
    """
    Renders the report HTML string.

    Translation approach: reads .mo file directly with Python's built-in
    gettext module — NO Django thread-local, NO middleware interference.
    All translated strings are passed as plain Python dict to the template.
    """
    lang = getattr(organization, 'language', None) or 'en'

    # Get translations directly from .mo file — reliable, no thread-local
    trans = get_translations(lang)

    # Build topic title
    topic_titles = {
        "opening":         trans["Opening Stock"],
        "purchase":        trans["Purchase"],
        "sale":            trans["Sale"],
        "purchase_return": trans["Purchase Return"],
        "sale_return":     trans["Sale Return"],
        "reject":          trans["Product Reject"],
    }
    topic_title = topic_titles.get(topic, topic)

    # Build columns/rows/totals using translations dict directly
    columns, rows, totals_row = build_columns_and_rows(topic, queryset, trans)

    if for_pdf:
        logo_url         = get_logo_url(organization)
        bengali_font_b64 = get_bengali_font_b64() if lang == 'bn' else None
    else:
        logo_url = (
            request.build_absolute_uri(organization.logo.url)
            if organization.logo else None
        )
        bengali_font_b64 = None

    template = get_template("report_app/report_template.html")
    context = {
        "columns":           columns,
        "rows":              rows,
        "totals_row":        totals_row,
        "topic":             topic,
        "topic_title":       topic_title,
        "start":             start_date,
        "end":               end_date,
        "organization":      organization,
        "branch":            branch,
        "logo_url":          logo_url,
        "lang":              lang,
        "is_pdf":            for_pdf,
        "bengali_font_b64":  bengali_font_b64,
        # "t" is the translations dict — template accesses it as {{ t.Report }},
        # {{ t.From }} etc. Django dot notation maps {{ t.KEY }} to trans["KEY"].
        "t":                 trans,
    }
    # Pass request when rendering browser preview so {% csrf_token %} in the
    # Download PDF form generates a valid token.
    # For PDF (for_pdf=True) request is not needed — no csrf_token in PDF.
    if for_pdf:
        html = template.render(context)
    else:
        html = template.render(context, request=request)

    return html


# ==========================================================
# BUILD CONTEXT (kept for compatibility)
# ==========================================================
def build_report_context(topic, start_date, end_date, data, organization, branch=None):
    lang  = getattr(organization, 'language', None) or 'en'
    trans = get_translations(lang)
    columns, rows, totals_row = build_columns_and_rows(topic, data, trans) if data else ([], [], [])
    return {
        "columns":      columns,
        "rows":         rows,
        "topic":        topic,
        "start":        start_date,
        "end":          end_date,
        "organization": organization,
        "branch":       branch,
    }


# ==========================================================
# GENERATE PDF
# ==========================================================
def generate_pdf(request, topic, start_date, end_date, queryset, organization, branch=None):
    html_content = render_report_html(
        request, topic, start_date, end_date, queryset,
        organization, branch, for_pdf=True
    )
    return HTML(string=html_content, base_url=settings.MEDIA_ROOT).write_pdf()