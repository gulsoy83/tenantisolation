from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import JSONField
from django.utils.translation import gettext_lazy as _

# WARNING: This code has not been tested yet.
# Be cautious when overriding the core manager, especially since TenantCoreModel depends on CoreModel.

# class CoreQuerySet(models.QuerySet):
#     def create(self, **kwargs):
#         user = kwargs.pop("user", None)
#         reverse_one_to_one_fields = frozenset(kwargs).intersection(
#             self.model._meta._reverse_one_to_one_field_names
#         )
#         if reverse_one_to_one_fields:
#             raise ValueError(
#                 "The following fields do not exist in this model: %s"
#                 % ", ".join(reverse_one_to_one_fields)
#             )

#         obj = self.model(**kwargs)
#         self._for_write = True
#         obj.save(force_insert=True, using=self.db, user=user)
#         return obj


# class CoreManager(models.Manager):
#     def get_queryset(self):
#         return CoreQuerySet(self.model, using=self._db)


class CoreModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created_by",
        verbose_name=_("Created By"),
    )
    updated_at = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Updated At")
    )
    updated_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated_by",
        verbose_name=_("Updated By"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Deleted At")
    )
    deleted_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted_by",
        verbose_name=_("Deleted By"),
    )
    data = JSONField(null=True, blank=True, default=dict)
    # objects = CoreManager()

    def __str__(self):
        return str(self.id)

    class Meta:
        abstract = True
        ordering = ["id"]

    def save(
        self,
        user=None,
        *args,
        **kwargs,
    ):
        assert user, _("User parameter is missing.")

        # TODO: The `deleted_by` field should be populated upon soft delete.
        is_new = self._state.adding
        if is_new:
            self.created_by = user
        else:
            self.updated_by = user

        super().save(*args, **kwargs)