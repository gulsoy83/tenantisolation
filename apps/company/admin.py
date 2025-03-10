from django.contrib import admin
from core.admin import CoreAdmin
from tenant.admin import TenantCoreAdmin
from .models import (
    Company,
    ExpenseType,
    Expense
)


@admin.register(Company)
class CompanyAdmin(CoreAdmin):
    list_display = [
        "code",
        "legal_name",
        "tax_office",
    ]
    search_fields = ["legal_name", "tax_office"]
    autocomplete_fields = [
        "created_by",
        "updated_by",
        "deleted_by",
    ]


@admin.register(Expense)
class ExpenseAdmin(TenantCoreAdmin):
    list_display = [
        "expense_type",
        "amount",
        "date",
    ]
    search_fields = [
        "explanation",
        "expense_type__name",
    ]
    autocomplete_fields = [
        "created_by",
        "updated_by",
        "deleted_by",
        "tenant_company",
        "expense_type",
        "approved_by",
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "expense_type":
            kwargs["queryset"] = ExpenseType.objects.filter(tenant_user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ExpenseType)
class ExpenseTypeAdmin(TenantCoreAdmin):
    list_display = ["name", "tenant_company"]
    search_fields = ["name"]
    autocomplete_fields = [
        "created_by",
        "updated_by",
        "deleted_by",
        "tenant_company",
    ]