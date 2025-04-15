from django.db import models
from django.utils.translation import gettext_lazy as _


class CreatedAtMixin(models.Model):
    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True,
    )

    class Meta:
        abstract = True
