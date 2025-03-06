from django.contrib import admin
from core.admin import CoreAdmin
from constance import config as constance_config


class TenantCoreAdmin(CoreAdmin):
    """
    Querysets for the select/autocomplete fields must be overrided separately.
    """

    # This will prevent the appearance of the rows from another tenants in admin page.
    """
    def get_queryset(self, request):
        qs = Model1.objects.all(tenant_user=request.user)
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    """

    # Adjust the querysets for the isolated FK fields; otherwise, they will return queryset.none() due to the missing tenant_user parameter."
    """
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "employee":
            kwargs["queryset"] = Employee.objects.filter(tenant_user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    """

    # This will prevent the appearance of the objects from other tenants in autocomplete list.
    """
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        from dal import autocomplete
        form.base_fields['field1'].widget = autocomplete.ModelSelect2(
            url='field1-autocomplete',
        )
        return form
    """

    def get_queryset(self, request):
        if constance_config.ADMIN_SITE_ISOLATION:
            qs = self.model._default_manager.get_queryset().none()
            if hasattr(self.model, "objects"):
                qs = self.model.objects.tenant_isolated_queryset(
                    tenant_user=request.user
                )
        else:
            qs = self.model._default_manager.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
