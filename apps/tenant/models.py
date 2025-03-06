from sentry_sdk import capture_exception
from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
    ValidationError,
)
from core.models import CoreModel
from core.cache_keys import SELECTED_TCID_CACHE_KEY


class TenantQuerySet(models.QuerySet):
    def create(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        assert user, _(
            "Tenant User parameter is required, for: TenantQuerySet.create()"
        )

        reverse_one_to_one_fields = frozenset(kwargs).intersection(
            self.model._meta._reverse_one_to_one_field_names
        )
        if reverse_one_to_one_fields:
            raise ValueError(
                "The following fields do not exist in this model: %s"
                % ", ".join(reverse_one_to_one_fields)
            )

        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(force_insert=True, using=self.db, user=user)
        return obj

    def get_or_create(self, defaults=None, **kwargs):
        user = kwargs.pop("tenant_user", None)
        assert user, _(
            "Tenant User parameter is required, for: TenantQuerySet.get_or_create()"
        )

        from django.db.utils import IntegrityError
        from django.db import transaction
        from django.db.models.utils import (
            resolve_callables,
        )

        self._for_write = True
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            params = self._extract_model_params(defaults, **kwargs)
            try:
                with transaction.atomic(using=self.db):
                    params = dict(resolve_callables(params))
                    return self.create(tenant_user=user, **params), True
            except IntegrityError:
                try:
                    return self.get(**kwargs), False
                except self.model.DoesNotExist:
                    pass
                raise

    def update_or_create(self, defaults=None, create_defaults=None, **kwargs):
        user = kwargs.pop("tenant_user", None)
        assert user, _(
            "Tenant User parameter is required, for: TenantQuerySet.update_or_create()"
        )

        from django.db import transaction
        from django.db.models import Field
        from django.db.models.utils import (
            resolve_callables,
        )

        update_defaults = defaults or {}
        if create_defaults is None:
            create_defaults = update_defaults

        self._for_write = True
        with transaction.atomic(using=self.db):
            obj, created = self.select_for_update().get_or_create(
                create_defaults, tenant_user=user, **kwargs
            )
            if created:
                return obj, created
            for k, v in resolve_callables(update_defaults):
                setattr(obj, k, v)

            update_fields = set(update_defaults)
            concrete_field_names = self.model._meta._non_pk_concrete_field_names
            if concrete_field_names.issuperset(update_fields):
                for field in self.model._meta.local_concrete_fields:
                    if not (
                        field.primary_key or field.__class__.pre_save is Field.pre_save
                    ):
                        update_fields.add(field.name)
                        if field.name != field.attname:
                            update_fields.add(field.attname)
                obj.save(user=user, using=self.db, update_fields=update_fields)
            else:
                obj.save(user=user, using=self.db)
        return obj, False


class TenantCoreManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    @classmethod
    def __get_tenant_company_id_from_db(cls, tenant_user):
        try:
            from account.models import AccountCompany

            account = tenant_user.account
            account_company = AccountCompany.objects.get(
                account=account, is_selected=True
            )
            return account_company.company_id
        except Exception as exc:
            capture_exception(exc)
            return None

    @classmethod
    def __get_tenant_company_id(cls, tenant_user):
        tenant_id = cache.get(
            f"{SELECTED_TCID_CACHE_KEY}_{tenant_user.id}",
            None,
        )
        if not tenant_id:
            tenant_id = cls.__get_tenant_company_id_from_db(tenant_user=tenant_user)
            if tenant_id:
                cache.set(
                    f"{SELECTED_TCID_CACHE_KEY}_{tenant_user.id}",
                    tenant_id,
                    timeout=None,
                )
        return tenant_id

    def __filter_by_tenant(self, queryset, tenant_user=None, **kwargs):
        tenant_filter_kwargs = {}
        """
        Note: The **kwargs contains all of the original query parameters.
        """
        # ============ Direct Filtering ============
        tenant_company_id = kwargs.get("tenant_company_id", None)
        tenant_company = kwargs.get("tenant_company", None)
        if tenant_company or tenant_company_id:
            if tenant_company:
                tenant_filter_kwargs["tenant_company"] = tenant_company
            elif tenant_company_id:
                tenant_filter_kwargs["tenant_company_id"] = tenant_company_id
            return queryset.filter(**tenant_filter_kwargs)
        # ==========================================
        if not tenant_user:
            return queryset.none()
        tenant_company_id = self.__get_tenant_company_id(tenant_user=tenant_user)
        if tenant_company_id:
            tenant_filter_kwargs["tenant_company_id"] = tenant_company_id
        else:
            return queryset.none()
        return queryset.filter(**tenant_filter_kwargs)

    def all(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs)

    def reverse(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).reverse()

    def filter(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(),
            tenant_user=user,
            **kwargs,
        ).filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        try:
            qs = self.__filter_by_tenant(
                super().all(),
                tenant_user=user,
                **kwargs,
            )
            return qs.get(*args, **kwargs)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist(
                _("No matching objects found for the current tenant.")
            )
        except MultipleObjectsReturned:
            raise MultipleObjectsReturned(
                _("Multiple objects returned for the current tenant.")
            )
        except Exception as exc:
            capture_exception(exc)
            raise exc

    def exclude(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).exclude(*args, **kwargs)

    def first(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).first()

    def last(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs).last()

    def order_by(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).order_by(*args)

    def count(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).count()

    def exists(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).exists()

    def earliest(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).earliest(*args)

    def latest(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).latest(*args)

    def distinct(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).distinct(*args)

    def using(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs).using(
            *args
        )

    def iterator(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).iterator()

    def select_related(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).select_related(*args)

    def prefetch_related(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).prefetch_related(*args)

    def values(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).values(*args, **kwargs)

    def values_list(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).values_list(*args, **kwargs)

    def alias(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs).alias(
            *args, **kwargs
        )

    def aggregate(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).aggregate(*args, **kwargs)

    def annotate(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).annotate(*args, **kwargs)

    def extra(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs).extra(
            **kwargs
        )

    def dates(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs).dates(
            *args, **kwargs
        )

    def datetimes(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).datetimes(*args, **kwargs)

    def union(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs).union(
            *args, **kwargs
        )

    def intersection(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).intersection(*args)

    def difference(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).difference(*args)

    def defer(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs).defer(
            *args
        )

    def only(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(super().all(), tenant_user=user, **kwargs).only(
            *args
        )

    def select_for_update(self, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).select_for_update(**kwargs)

    """
    Not completed methods

    def raw(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        try:
            ...
            return super().raw(*args, **kwargs)
        except Exception as exc:
            return super().none()

    bulk_create()
    bulk_update()
    in_bulk()
    contains()
    update()
    delete()
    as_manager()
    explain()
    """

    ####################################################################
    #                     Customized QS Methods                        #
    ####################################################################

    def create(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).create(tenant_user=user, **kwargs)

    def get_or_create(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).get_or_create(tenant_user=user, **kwargs)

    def update_or_create(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(
            super().all(), tenant_user=user, **kwargs
        ).update_or_create(tenant_user=user, **kwargs)

    ####################################################################

    def tenant_get_object_or_404(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        from django.shortcuts import get_object_or_404

        qs = self.__filter_by_tenant(self.get_queryset(), tenant_user=user, **kwargs)
        return get_object_or_404(qs, *args, **kwargs)

    def tenant_get_list_or_404(self, *args, **kwargs):
        user = kwargs.pop("tenant_user", None)
        from django.shortcuts import get_list_or_404

        qs = self.__filter_by_tenant(self.get_queryset(), tenant_user=user, **kwargs)
        return get_list_or_404(qs, *args, **kwargs)

    def tenant_isolated_queryset(self, **kwargs):
        qs = super().get_queryset()
        user = kwargs.pop("tenant_user", None)
        return self.__filter_by_tenant(qs, tenant_user=user, **kwargs)


class TenantCoreModel(CoreModel):
    """
    Abstract base model for tenant-specific data management.

    This model includes a `tenant_company_id` field which is used to filter records
    by the current tenant. The `tenant_company_id` is initially allowed to be null
    and blank because it will be set by the `save()` method before the model is saved
    to the database.

    Once set, `tenant_company_id` will be marked as `editable=False` to prevent
    modifications and ensure that it reflects the tenant-specific context accurately.
    """

    tenant_company = models.ForeignKey(
        "company.Company",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("Tenant Company"),
    )
    objects = TenantCoreManager()

    class Meta:
        abstract = True

    def save(self, disable_safety_checks=False, *args, **kwargs):
        user = kwargs.get("user", None)
        assert user, _("Tenant User parameter is missing.")

        # --- For debugging: uncomment while creating obj from admin panel. ---
        # cache_key = "tenant_company_id_1"
        # from django.contrib.auth.models import User
        # user = User.objects.get(id=1)

        tenant_company_id = cache.get(f"{SELECTED_TCID_CACHE_KEY}_{user.id}", None)
        if not tenant_company_id:
            tenant_company_id = getattr(
                self.__class__.objects,
                f"_{TenantCoreManager.__name__}__get_tenant_company_id_from_db",
            )(tenant_user=user)

        # -- Validate the tenant_company_id --
        assert tenant_company_id, _(
            "Tenant Company ID could not be retrieved from the cache or the database."
        )

        from account.models import AccountCompany
        from company.models import Company

        company_exists = Company.objects.filter(id=tenant_company_id).exists()
        accountcompany_exists = AccountCompany.objects.filter(
            company_id=tenant_company_id
        ).exists()

        assert company_exists, _("Tenant Company ID is not valid.")
        assert accountcompany_exists, _(
            "There is no AccountCompany associated with this Tenant Company ID."
        )
        # ------

        # Override the object's tenant_company field, if it is not already set.
        if not self.tenant_company_id:
            self.tenant_company_id = tenant_company_id
        else:
            # The object belongs to a specific tenant.
            if not disable_safety_checks:
                # Prevent saving if the object does not belong to the user.
                assert self.tenant_company_id == tenant_company_id, _(
                    "The Tenant Company ID fetched from the cache does not match the Tenant Company ID of the object."
                )
                # This will prevent the superuser from updating objects belonging to other tenants, but the superuser can change the tenant of those objects to their own.
                # TODO: Should this be allowed?
                # Isolating rows in the admin panel by tenant, appears to have fixed this issue.

        # Additional checks
        try:
            pass
        except Exception as exc:
            raise ValidationError(
                _(
                    "An unexpected error occurred while validating the Tenant Company ID."
                )
            )
        super().save(*args, **kwargs)
