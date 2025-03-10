import logging

from sentry_sdk import capture_exception
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from core.decorators import requires_admin_role, requires_superuser
from company.models import Company, Expense, ExpenseType

logger = logging.getLogger(__name__)

@login_required
@requires_superuser
def company_list(request):
    companies = Company.objects.filter(is_active=True, is_deleted=False)
    datas = []
    for x in companies:
        datas.append((x._json()))
    return JsonResponse({"data": datas})

@login_required
def expense_type_list(request):
    user = request.user

    expenses = ExpenseType.objects.filter(tenant_user=user).filter(is_active=True, is_deleted=False)
    datas = []
    for x in expenses:
        datas.append((x._json()))
    return JsonResponse({"data": datas})

@login_required
def expense_list(request):
    user = request.user

    expenses = Expense.objects.filter(tenant_user=user).filter(is_active=True, is_deleted=False)
    datas = []
    for x in expenses:
        datas.append((x._json()))
    return JsonResponse({"data": datas})