# Generated by Django 5.2 on 2025-04-15 15:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
            },
        ),
        migrations.CreateModel(
            name='Ad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок')),
                ('description', models.TextField(verbose_name='Описание')),
                ('image_url', models.URLField(blank=True, default=None, null=True, verbose_name='Ссылка на изображение')),
                ('condition', models.CharField(choices=[('new', 'Новое'), ('like_new', 'Как новое'), ('used_good', 'Б/У - Хорошее состояние'), ('used_fair', 'Б/У - Удовлетворительное состояние'), ('used_poor', 'Б/У - Плохое состояние')], max_length=50, verbose_name='Состояние товара')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ads', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ads', to='ads.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Объявление',
                'verbose_name_plural': 'Объявления',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExchangeProposal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('comment', models.TextField(blank=True, default=None, null=True, verbose_name='Комментарий')),
                ('status', models.CharField(choices=[('pending', 'Ожидает'), ('accepted', 'Принята'), ('rejected', 'Отклонена')], default='pending', max_length=20, verbose_name='Статус')),
                ('ad_receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_proposals', to='ads.ad', verbose_name='Целевое объявление')),
                ('ad_sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_proposals', to='ads.ad', verbose_name='Предлагаемое объявление')),
            ],
            options={
                'verbose_name': 'Предложение обмена',
                'verbose_name_plural': 'Предложения обмена',
                'ordering': ['-created_at'],
                'unique_together': {('ad_sender', 'ad_receiver')},
            },
        ),
    ]
