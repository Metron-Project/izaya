from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .lookups import registry


@require_GET
def search(request, name):
    if name not in registry:
        raise Http404
    lookup = registry[name]()
    if not lookup.has_access(request):
        raise PermissionDenied

    # PostgreSQL rejects NUL characters in query parameters.
    query = request.GET.get("q", "").replace("\x00", "").strip()
    if not query:
        return HttpResponse()

    context = {"items": []}
    if len(query) < lookup.min_length:
        context["message"] = lookup.min_length_text % {"count": lookup.min_length}
    else:
        results = list(lookup.search(query, request)[: lookup.max_results + 1])
        context["items"] = [lookup.to_item(result) for result in results[: lookup.max_results]]
        if not results:
            context["message"] = lookup.no_results_text
        elif len(results) > lookup.max_results:
            context["message"] = lookup.more_results_text % {"count": lookup.max_results}
    return render(request, "izaya/options.html", context)
