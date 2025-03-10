import uuid
from datetime import datetime

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import CoreModel
from tenant.models import TenantCoreModel


class Company(CoreModel):
    CACHE_KEY = "company"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_name = models.CharField(max_length=256, verbose_name=_("Legal Name"))
    tax_office = models.CharField(max_length=24, verbose_name=_("Tax Office"))
    tax_no = models.CharField(max_length=256, unique=True, verbose_name=_("Tax No"))
    code = models.CharField(
        max_length=64, unique=True, null=True, blank=True, verbose_name=_("Code")
    )
    website = models.CharField(
        max_length=128, null=True, blank=True, verbose_name=_("Website")
    )
    email = models.EmailField(
        max_length=128, null=True, blank=True, verbose_name=_("Email")
    )

    class Meta:
        ordering = ["legal_name"]

    def __str__(self):
        return f"{self.legal_name}{' - ' + self.code if self.code else ''}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        # The unique=True and null=True options should not be used together with CharField unless you apply the fix described below.
        if not self.code:
            self.code = None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def _json(self):
        return {
            "id": self.id,
            "legal_name": self.legal_name,
            "tax_office": self.tax_office,
            "tax_no": self.tax_no,
            "code": self.code,
            "website": self.website,
            "email": self.email,
        }


    def get_company_owner(self):
        from native_account.models import RoleChoices

        account_company = self.accountcompany_set.filter(
            role=RoleChoices.OWNER, is_active=True, is_deleted=False
        ).first()
        if account_company:
            return account_company.account
        return None



class ExpenseType(TenantCoreModel):
    CACHE_KEY = "expense_type"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(verbose_name=_("Name"))

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "tenant_company"],
                name="unique_expense_type_name",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}"

    def _json(self):
        return {
            "id": self.id,
            "name": self.name,
            "tenant_company": self.tenant_company.legal_name,
        }

class Expense(TenantCoreModel):
    CACHE_KEY = "expense"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense_type = models.ForeignKey(
        "company.ExpenseType", on_delete=models.PROTECT, verbose_name=_("Expense Type")
    )
    date = models.DateTimeField(verbose_name=_("Date"), null=True, blank=True)
    amount = models.DecimalField(
        max_digits=9,  # 1 million
        decimal_places=2,
        default=0.00,
        verbose_name=_("Amount"),
    )
    explanation = models.TextField(verbose_name=_("Explanation"), null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name=_("Is Approved"))
    approved_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Approved By"),
    )
    approved_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Approved At")
    )
    is_paid = models.BooleanField(default=False, verbose_name=_("Is Paid"))
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Paid At"))

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        date_str = f" ({self.date.strftime('%d-%m-%Y %H:%M')})" if self.date else ""

        return f"{self.expense_type} : {self.amount}{date_str}"

    def _json(self):
        return {
            "id": self.id,
            "expense_type": str(self.expense_type),
            "amount": self.amount,
            "explanation": self.explanation,
            "date": self.date.strftime("%Y-%m-%d %H:%M:%S") if self.date else "",
            "is_approved": self.is_approved,
            "approved_at": self.approved_at.strftime("%Y-%m-%d %H:%M:%S")
            if self.approved_at
            else "",
            "approved_by": self.approved_by.get_full_name() if self.approved_by else "",
            "is_paid": self.is_paid,
            "paid_at": self.paid_at.strftime("%Y-%m-%d %H:%M:%S")
            if self.paid_at
            else "",
            "tenant_company": self.tenant_company.legal_name,
        }