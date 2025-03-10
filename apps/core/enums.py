from django.db import models
from enum import Enum
from django.utils.translation import gettext_lazy, gettext


class CoreTextChoices(models.TextChoices):
    @classmethod
    def example_method(cls):
        """Placeholder for future methods."""
        pass


class CoreIntegerChoices(models.IntegerChoices):
    @classmethod
    def example_method(cls):
        """Placeholder for future methods."""
        pass


class CoreEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: [c.name, c.value], cls))

    @classmethod
    def get(cls, name):
        return cls[name].value

    @classmethod
    def get_values(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def choose_list(cls):
        return list(
            map(
                lambda c: [
                    c.value,
                    gettext_lazy(
                        " ".join(x.capitalize() or "_" for x in c.value.split("_"))
                    ),
                ],
                cls,
            )
        )

    def localize(self):
        label = " ".join(x.capitalize() or "_" for x in self.value.split("_"))
        return gettext(label)
