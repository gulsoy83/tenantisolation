import logging

from constance import config as constance_config
from dal import autocomplete
from sentry_sdk import capture_exception
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from core.decorators import requires_admin_role, requires_owner_role
from native_account.models import AccountCompany
logger = logging.getLogger(__name__)


@login_required
def accountcompany_change(request):
    post = request.POST
    get = request.GET
    user = request.user

    tenant_company_id = post.get("tenant_company_id", None) or get.get("tenant_company_id", None)

    if user.is_authenticated and tenant_company_id:
        try:
            from core.cache_keys import SELECTED_TCID_CACHE_KEY

            account = user.account

            selected_obj = AccountCompany.objects.get(
                account=account, company_id=tenant_company_id
            )
            selected_obj.is_selected = True
            selected_obj.save(user=request.user)

            cache.set(
                f"{SELECTED_TCID_CACHE_KEY}_{user.id}",
                selected_obj.company_id,
                timeout=None,
            )

            return JsonResponse(
                {
                    "result": "success",
                    "message": _(
                        "Selected Tenant Company has been changed successfully."
                    ),
                }
            )
        except Exception as exc:
            return JsonResponse({"result": False, "message": str(exc)})

    return JsonResponse({"result": False, "message": _("No selection has been made.")})