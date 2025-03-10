from django.urls import path
from company import views

urlpatterns = [
    path("list/", views.company_list, name="company-list"),
    path("expense/list/", views.expense_list, name="expense-list"),
    path("expense-type/list/", views.expense_type_list, name="expense-type-list"),
]