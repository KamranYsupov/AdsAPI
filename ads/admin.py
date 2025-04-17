from django.contrib import admin

from .models import Ad, Category, ExchangeProposal


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(ExchangeProposal)
class ExchangeProposalAdmin(admin.ModelAdmin):
    pass