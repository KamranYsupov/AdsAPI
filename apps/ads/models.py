from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from db.model_mixins import CreatedAtMixin

User = get_user_model()


class Ad(CreatedAtMixin):
    """Модель объявления"""

    CONDITION_CHOICES = [
        ('new', _('Новое')),
        ('like_new', _('Как новое')),
        ('used_good', _('Б/У - Хорошее состояние')),
        ('used_fair', _('Б/У - Удовлетворительное состояние')),
        ('used_poor', _('Б/У - Плохое состояние')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ads',
        verbose_name=_('Пользователь')
    )
    title = models.CharField(
        _('Заголовок'),
        max_length=200
    )
    description = models.TextField(_('Описание'))
    image_url = models.URLField(
        _('Ссылка на изображение'),
        blank=True,
        null=True,
        default=None
    )
    category = models.ForeignKey(
        'ads.Category',
        related_name='ads',
        verbose_name=_('Категория'),
        on_delete = models.SET_NULL,
        null = True,
    )
    condition = models.CharField(
        _('Состояние товара'),
        max_length=50,
        choices=CONDITION_CHOICES
    )
    is_active = models.BooleanField(_('Активно'), default=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    class Meta:
        verbose_name = _('Объявление')
        verbose_name_plural = _('Объявления')
        ordering = ['-created_at']


class ExchangeProposal(CreatedAtMixin):
    """Модель предложения обмена"""

    class Status:
        WAITING = 'pending'
        ACCEPTED = 'accepted'
        REJECTED = 'rejected'

        CHOICES = [
            (WAITING, _('Ожидает')),
            (ACCEPTED, _('Принята')),
            (REJECTED, _('Отклонена')),
        ]

    ad_sender = models.ForeignKey(
        'ads.Ad',
        on_delete=models.CASCADE,
        related_name='sent_proposals',
        verbose_name=_('Предлагаемое объявление')
    )
    ad_receiver = models.ForeignKey(
        'ads.Ad',
        on_delete=models.CASCADE,
        related_name='received_proposals',
        verbose_name=_('Целевое объявление')
    )
    comment = models.TextField(
        _('Комментарий'),
        blank=True,
        null=True,
        default=None
    )
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.CHOICES,
        default=Status.WAITING
    )

    def __str__(self):
        return _("Предложение обмена №{}").format(self.id)

    class Meta:
        verbose_name = _('Предложение обмена')
        verbose_name_plural = _('Предложения обмена')
        ordering = ['-created_at']
        unique_together = ['ad_sender', 'ad_receiver']


class Category(models.Model):
    """Модель категории"""

    name = models.CharField(
        _('Название'),
        max_length=50,
        unique=True,
    )

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')

    def __str__(self):
        return self.name