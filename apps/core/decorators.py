from functools import wraps

from core.utils import conn_replica
from django.db import connections
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def requires_superuser(view):
    @wraps(view)
    def _view(request, *args, **kwargs):
        user = request.user

        if not user.is_superuser:
            messages.error(
                request, ("You do not have permission to access this resource.")
            )
            return redirect(reverse("main-page"))

        return view(request, *args, **kwargs)

    return _view


def requires_admin_role(view):
    @wraps(view)
    def _view(request, *args, **kwargs):
        user = request.user

        from native_account.models import RoleChoices

        try:
            cursor = conn_replica(connections)
            sql = """
                SELECT role
                FROM native_account_accountcompany ac
                JOIN native_account_account aa on ac.account_id = aa.id
                JOIN auth_user au on aa.user_id = au.id
                WHERE au.id = %s and ac.is_selected = true
                LIMIT 1
            """
            cursor.execute(sql, [user.id])
            row = cursor.fetchone()
            selected_account_company_role = int(row[0]) if row else None
            """
            ORM Version for Future Reference
            selected_account_company_role = (
                AccountCompany.objects.filter(account=user.account, is_selected=True)
                .values_list("role", flat=True)
                .first()
            )
            """
        except Exception:
            selected_account_company_role = None

        if selected_account_company_role not in [RoleChoices.ADMIN, RoleChoices.OWNER]:
            messages.error(
                request, ("You do not have permission to access this resource.")
            )
            return redirect(reverse("main-page"))

        return view(request, *args, **kwargs)

    return _view


def requires_owner_role(view):
    @wraps(view)
    def _view(request, *args, **kwargs):
        user = request.user

        from native_account.models import RoleChoices

        try:
            cursor = conn_replica(connections)
            sql = """
                SELECT role
                FROM native_account_accountcompany ac
                JOIN native_account_account aa on ac.account_id = aa.id
                JOIN auth_user au on aa.user_id = au.id
                WHERE au.id = %s and ac.is_selected = true
                LIMIT 1
            """
            cursor.execute(sql, [user.id])
            row = cursor.fetchone()
            selected_account_company_role = int(row[0]) if row else None
            """
            ORM Version for Future Reference
            selected_account_company_role = (
                AccountCompany.objects.filter(account=user.account, is_selected=True)
                .values_list("role", flat=True)
                .first()
            )
            """
        except Exception:
            selected_account_company_role = None

        if selected_account_company_role != RoleChoices.OWNER:
            messages.error(
                request, ("You do not have permission to access this resource.")
            )
            return redirect(reverse("main-page"))

        return view(request, *args, **kwargs)

    return _view
