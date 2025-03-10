from constance import config as constance_config
from core.utils import conn_replica
from sentry_sdk import capture_exception
from django.utils.translation import gettext as _
from django.db import connections


def user_info(request):
    user = request.user
    user_full_name, user_first_name_latter, user_last_name_latter = "", "", ""
    if user.is_authenticated:
        user_full_name = user.get_full_name()
        user_first_name_latter = user.first_name[0] if user.first_name else ""
        user_last_name_latter = user.last_name[0] if user.last_name else ""

    return {
        "user_full_name": user_full_name,
        "user_first_name_latter": user_first_name_latter,
        "user_last_name_latter": user_last_name_latter,
    }


def account_info(request):
    user = request.user
    tenant_company_id = None
    tenant_company_name = ""
    available_tenant_companies = []

    if user.is_authenticated:
        try:
            assert hasattr(user, "account"), _("User must have an account.")
            account = user.account

            try:
                """
                ORM Version for Future Reference
                available_tenant_companies = AccountCompany.objects.filter(
                    account=account,
                    is_selected=False,
                    is_active=True,
                    is_deleted=False,
                ).values_list("company_id", "company__legal_name")
                """
                cursor = conn_replica(connections)
                sql = """
                    SELECT cc.id, cc.legal_name
                    FROM native_account_accountcompany ac
                    JOIN native_account_account aa ON ac.account_id = aa.id
                    JOIN company_company cc ON ac.company_id = cc.id
                    WHERE ac.account_id = %s AND ac.is_selected = false AND ac.is_active = true AND ac.is_deleted = false
                """
                cursor.execute(sql, [account.id])
                rows = cursor.fetchall()
                available_tenant_companies = [
                    (str(row[0]), str(row[1])) for row in rows
                ]
            except Exception as sql_exc:
                available_tenant_companies = []
                capture_exception(sql_exc)

            selected_tenant_company_id = account.selected_tenant_company_id
            if selected_tenant_company_id:
                try:
                    """
                    ORM Version for Future Reference
                    tc_legal_name = (
                        Company.objects.filter(id=selected_account_company_id)
                        .values_list("legal_name", flat=True)
                        .first()
                    )
                    """
                    cursor = conn_replica(connections)
                    sql = """
                        SELECT legal_name
                        FROM company_company cc
                        WHERE cc.id = %s
                    """
                    cursor.execute(sql, [selected_tenant_company_id])
                    row = cursor.fetchone()
                    tc_legal_name = str(row[0]) if row else None
                except Exception as sql_exc:
                    tc_legal_name = None
                    capture_exception(sql_exc)

                if tc_legal_name:
                    tenant_company_id = selected_tenant_company_id
                    tenant_company_name = tc_legal_name
        except AssertionError as aexc:
            pass
        except Exception as exc:
            capture_exception(exc)

    return {
        "tenant_company_id": tenant_company_id,
        "tenant_company_name": tenant_company_name,
        "available_tenant_companies": available_tenant_companies,
    }
