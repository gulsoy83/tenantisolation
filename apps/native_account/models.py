import random
import uuid
from datetime import datetime
from typing import Union

from core.utils import conn_replica
from constance import config as constance_config
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction, connections
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_exception

from core.enums import CoreIntegerChoices
from core.models import CoreModel
from company.models import Company


class RoleChoices(CoreIntegerChoices):
    OWNER = 0, _("Owner")
    ADMIN = 1, _("Admin")
    MEMBER = 2, _("Member")

class Account(CoreModel):
    CACHE_KEY = "account"
    EMAIL_VERIFICATION_CACHE_KEY = "account_email_verification"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        "auth.User", on_delete=models.PROTECT, verbose_name=_("User")
    )
    phone = models.CharField(max_length=128, verbose_name=_("Phone"))
    is_phone_verified = models.BooleanField(
        default=False, verbose_name=_("Is Phone Verified")
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name=_("Birth Date"))
    is_email_verified = models.BooleanField(
        default=False, verbose_name=_("Is Email Verified")
    )
    email_verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Email Verified At")
    )

    @property
    def selected_company(self) -> Union[Company, None]:
        account_company = self.accountcompany_set.filter(is_selected=True).first()
        return account_company.company if account_company else None

    @property
    def selected_tenant_company_id(self) -> Union[str, None]:
        return AccountCompany.get_selected_tenant_company_id(self.user)

    def __str__(self):
        return self.user.email

    def clean(self):
        current_email = self.user.email
        if not current_email:
            raise ValidationError(_("User email is required."))
        count = get_user_model().objects.filter(email__iexact=current_email).count()
        if count > 1:
            raise ValidationError(_("User email must be a unique value."))

    def save(self, user=None, *args, **kwargs):
        self.clean()
        super().save(user=user, *args, **kwargs)

    def set_email_as_verified(self, user=None):
        from datetime import datetime

        self.is_email_verified = True
        self.email_verified_at = datetime.now()
        self.save(user=user)


class AccountCompanyQuerySet(models.QuerySet):
    def delete(self):
        count = 0
        with transaction.atomic():
            for instance in self:
                instance.delete()
                count += 1
        return count


class AccountCompanyManager(models.Manager):
    def get_queryset(self):
        return AccountCompanyQuerySet(self.model, using=self._db)

    def delete(self):
        return self.get_queryset().delete()


class AccountCompany(CoreModel):
    CACHE_KEY = "account_company"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey("native_account.Account", on_delete=models.PROTECT)
    company = models.ForeignKey("company.Company", on_delete=models.PROTECT)
    is_selected = models.BooleanField(default=False, verbose_name=_("Is Selected"))
    role = models.IntegerField(
        choices=RoleChoices, default=RoleChoices.ADMIN, verbose_name=_("Role")
    )
    objects = AccountCompanyManager()

    def __str__(self):
        return (
            f"{str(self.account)} {self.company.legal_name} {self.get_role_display()}"
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "company"],
                name="unique_accountcompany",
            )
        ]
        ordering = ["-created_at"]

    def _json(self):
        return {
            "id": self.id,
            "account": str(self.account),
            "company": self.company.legal_name,
            "is_selected": self.is_selected,
            "role": self.role,
            "role_trans": self.get_role_display(),
        }

    def clean(self):
        selected_exists = (
            AccountCompany.objects.filter(account=self.account, is_selected=True)
            .exclude(id=self.id)
            .exists()
        )
        selected_qs = AccountCompany.objects.filter(
            account=self.account, is_selected=True
        ).exclude(id=self.id)

        if self.is_active and not self.is_deleted:
            if self.is_selected:
                if selected_exists:
                    # An AccountCompany with 'is_selected=True' already exists.
                    selected_qs.update(is_selected=False)
            elif not self.is_selected:
                if not selected_exists:
                    # There should be at least one object with is_selected=True
                    self.is_selected = True
        else:
            self.is_selected = False

        # Check if there's already an owner for this company
        owner_exists = (
            AccountCompany.objects.filter(company=self.company, role=RoleChoices.OWNER)
            .exclude(id=self.id)
            .exists()
        )

        if self.role == RoleChoices.OWNER and owner_exists:
            raise ValidationError(_("Invalid role, please contact with your company"))

    def save(self, *args, **kwargs):
        self.clean()
        is_initial_save = self._state.adding
        super().save(*args, **kwargs)

        if is_initial_save:
            try:
                with transaction.atomic():
                    ...
            except Exception as exc:
                capture_exception(exc)

        if self.is_selected:
            from core.cache_keys import SELECTED_TCID_CACHE_KEY

            cache.set(
                f"{SELECTED_TCID_CACHE_KEY}_{self.account.user.id}",
                self.company_id,
                timeout=None,
            )

    def delete(self, *args, **kwargs):
        user = self.account.user
        if self.is_selected:
            from core.cache_keys import SELECTED_TCID_CACHE_KEY

            cache.delete(f"{SELECTED_TCID_CACHE_KEY}_{self.account.user.id}")
        super().delete(*args, **kwargs)
        try:
            ac_next = AccountCompany.objects.filter(
                account=self.account,
            ).first()
            if ac_next:
                """
                This user is not the one who is performing the deletion process.
                However, it will be used in .save() because we don't have the specified parameter.
                Note that the .save() will trigger the .clean().
                """
                ac_next.save(user=user)
            with transaction.atomic():
                from django.contrib.sessions.models import Session

                for session in Session.objects.all():
                    data = session.get_decoded()
                    if str(user.id) == data.get("_auth_user_id"):
                        session.delete()
        except Exception as exc:
            capture_exception(exc)

    @classmethod
    def get_selected_tenant_company_id(cls, user=None) -> Union[str, None]:
        assert user, _("User parameter is missing.")
        try:
            cursor = conn_replica(connections)
            sql = """
                SELECT company_id
                FROM native_account_accountcompany ac
                JOIN native_account_account aa on ac.account_id = aa.id
                JOIN auth_user au on aa.user_id = au.id
                WHERE au.id = %s and ac.is_selected = true
                LIMIT 1
            """
            cursor.execute(sql, [user.id])
            row = cursor.fetchone()
            selected_company_id = str(row[0]) if row else None
            """
            ORM Version for Future Reference
            selected_company_id = (
                AccountCompany.objects.filter(account=user.account, is_selected=True)
                .values_list("company_id", flat=True)
                .first()
            )
            """
        except Exception as exc:
            capture_exception(exc)
            selected_company_id = None
        return selected_company_id

    @classmethod
    def get_isolated_account_ids(
        cls, user=None, tenant_company_id=None, admin_role_only=False
    ) -> list:
        if not user and not tenant_company_id:
            if not user:
                raise Exception(_("User parameter is missing."))
            raise Exception(_("Tenant Company ID is missing."))
        selected_company_id = (
            cls.get_selected_tenant_company_id(user=user) if user else tenant_company_id
        )
        try:
            assert selected_company_id, _("Selected Company ID is required.")
            filter_sql = ""
            params = [selected_company_id]
            if admin_role_only:
                filter_sql += """
                        AND (ac.role = %s OR ac.role = %s)
                    """
                params.extend([RoleChoices.ADMIN, RoleChoices.OWNER])
            cursor = conn_replica(connections)
            sql = (
                (
                    """
                    SELECT account_id
                    FROM native_account_accountcompany ac
                    WHERE ac.company_id = %s AND ac.is_active = true AND ac.is_deleted = false
                    """
                )
                + filter_sql
            )
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            account_ids = [str(row[0]) for row in rows]
            """
            ORM Version for Future Reference
            account_ids = AccountCompany.objects.filter(
                company_id=selected_company_id,
                is_active=True,
                is_deleted=False,
            ).values_list("account_id", flat=True)
            if admin_role_only:
                account_ids = account_ids.filter(
                    Q(role=RoleChoices.ADMIN) | Q(role=RoleChoices.OWNER)
                )
            """
        except Exception as exc:
            capture_exception(exc)
            account_ids = []
        return account_ids

    @classmethod
    def get_isolated_users_queryset(
        cls, user=None, tenant_company_id=None, admin_role_only=False
    ):
        if not user and not tenant_company_id:
            if not user:
                raise Exception(_("User parameter is missing."))
            raise Exception(_("Tenant Company ID is missing."))
        acc_ids = (
            cls.get_isolated_account_ids(user=user, admin_role_only=admin_role_only)
            if user
            else cls.get_isolated_account_ids(
                tenant_company_id=tenant_company_id, admin_role_only=admin_role_only
            )
        )
        try:
            assert acc_ids, _("Account IDs are required.")
            placeholders = ", ".join(["%s" for _ in range(len(acc_ids))])
            cursor = conn_replica(connections)
            sql = f"""
                SELECT user_id
                FROM native_account_account aa
                WHERE id IN ({placeholders}) AND is_active = true AND is_deleted = false
            """
            cursor.execute(sql, acc_ids)
            rows = cursor.fetchall()
            user_ids = [str(row[0]) for row in rows]
        except Exception as exc:
            capture_exception(exc)
            user_ids = []
        """
        ORM Version for Future Reference
        user_ids = Account.objects.filter(
            id__in=acc_ids,
            is_active=True,
            is_deleted=False,
        ).values_list("user_id", flat=True)
        """
        return get_user_model().objects.filter(id__in=user_ids)

    def is_deleteable(self, user=None):
        if self.role == RoleChoices.OWNER:
            return False
        return True
