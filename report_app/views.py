from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import translation
from .services import query_report, build_report_context, render_report_html, generate_pdf
from .utils import parse_localized_date


@login_required
def report_form(request):
    return render(request, "report_app/report_form.html")


@login_required
def preview_report(request):
    if request.method != "POST":
        return HttpResponse("Invalid request method.", status=405)

    org    = request.user.organization
    branch = getattr(request.user, 'branch', None)
    if org.branches.count() <= 1:
        branch = None

    # Get org language — this is the ONLY correct source
    lang = getattr(org, 'language', None) or 'en'

    # Parse dates using the org's locale
    start_date = parse_localized_date(request.POST.get("start_date"), locale=lang)
    end_date   = parse_localized_date(request.POST.get("end_date"),   locale=lang)
    topic      = request.POST.get("topic")

    # Use render_report_html (same as PDF but for_pdf=False) instead of
    # Django's render() shortcut.
    #
    # WHY: Django's render() returns a TemplateResponse on some builds and
    # a plain HttpResponse on others. In either case, {% trans %} tags in
    # the template are resolved lazily — AFTER our translation.deactivate()
    # runs in the finally block — so they fall back to English.
    #
    # render_report_html uses get_template().render() which is NOT lazy —
    # it returns a fully-rendered HTML string immediately, while the correct
    # language is still active. We wrap it in HttpResponse ourselves.
    html = render_report_html(
        request, topic, start_date, end_date,
        query_report(topic, start_date, end_date, org, branch),
        org, branch,
        for_pdf=False   # browser preview: logo as URL, font via Google Fonts
    )

    return HttpResponse(html)


@login_required
def download_report(request):
    if request.method != "POST":
        return HttpResponse("Invalid request method.", status=405)

    org    = request.user.organization
    branch = getattr(request.user, 'branch', None)
    if org.branches.count() <= 1:
        branch = None

    # Get org language — this is the ONLY correct source
    lang = getattr(org, 'language', None) or 'en'

    # Parse dates using the org's locale
    start_date = parse_localized_date(request.POST.get("start_date"), locale=lang)
    end_date   = parse_localized_date(request.POST.get("end_date"),   locale=lang)
    topic      = request.POST.get("topic")

    # generate_pdf → render_report_html handles language activation internally
    pdf_file = generate_pdf(
        request, topic, start_date, end_date,
        query_report(topic, start_date, end_date, org, branch),
        org, branch
    )

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={topic}_report.pdf"
    return response