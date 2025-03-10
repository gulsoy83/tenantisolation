from django.contrib import admin
from core.admin import CoreAdmin
from . import models


@admin.register(models.Account)
class AccountAdmin(CoreAdmin):
    list_display = ["user", "phone"]
    search_fields = ["user__username", "user__email"]
    autocomplete_fields = [
        "created_by",
        "updated_by",
        "deleted_by",
        "user",
    ]


@admin.register(models.AccountCompany)
class AccountCompanyAdmin(CoreAdmin):
    list_display = [
        "account",
        "role",
        "company",
        "is_selected",
        "is_active",
        "is_deleted",
    ]
    search_fields = ["account__user__username", "company__legal_name"]
    autocomplete_fields = [
        "created_by",
        "updated_by",
        "deleted_by",
        "account",
        "company",
    ]