from dal import autocomplete
from sentry_sdk import capture_exception
from collections import defaultdict
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _, get_language
from django.http import JsonResponse
from django.db.models import Q, F


@login_required
def home(request):
    post = request.POST
    user = request.user
    account = getattr(user, "account", None)

    name = request.user.get_full_name()
    last_login_at = user.last_login
    context = {"name": name, "last_login_at": last_login_at, "title": _("Home Page")}
    return render(request, "core/welcome.html", context)


def error_404(request, exception=None):
    return render(request, "error_404.html", status=404)


def error_500(request):
    return render(request, "error_500.html", status=500)
