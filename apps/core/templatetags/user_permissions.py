from django.template import Library
from django.db import connections
from core.utils import conn_replica

register = Library()


@register.filter
def has_permission(user, args) -> bool:
    permissions = args.split(",") if args else []

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
    except Exception as exc:
        selected_account_company_role = None

    permission_checks = {
        "superuser": user.is_superuser,
        "staff": user.is_staff,
        "admin_role": selected_account_company_role
        in [RoleChoices.ADMIN, RoleChoices.OWNER],
        "owner_role": selected_account_company_role == RoleChoices.OWNER,
    }

    user_granted_set = {perm for perm, granted in permission_checks.items() if granted}
    return all(_p in user_granted_set for _p in permissions)
