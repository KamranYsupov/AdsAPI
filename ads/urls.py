from django.urls import path
from . import views

urlpatterns = [
    path('', views.ad_list, name='ad_list'),
    path('create/', views.create_ad, name='ad_create'),
    path('<int:ad_id>/', views.ad_detail, name='ad_detail'),
    path('<int:ad_id>/edit/', views.edit_ad, name='ad_edit'),
    path('<int:ad_id>/delete/', views.delete_ad, name='ad_delete'),
    path('create_proposal/', views.create_proposal, name='proposal_create'),
    path('proposals/', views.exchange_proposal_list, name='proposal_list'),
    path('proposals/<int:proposal_id>/', views.proposal_detail, name='proposal_detail'),
    path('proposals/<int:proposal_id>/update/', views.update_proposal, name='proposal_update'),
]