from django.urls import path
from native_account import views

urlpatterns = [
    path(
        "accountcompany/change/",
        views.accountcompany_change,
        name="accountcompany-change",
    ),
]