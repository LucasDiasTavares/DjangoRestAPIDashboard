from .views import ExpensesCategorySumary, IncomeSourceSumary
from django.urls import path


urlpatterns = [
    path('expenses-category-sumary', ExpensesCategorySumary.as_view(), name="expenses-category-sumary"),
    path('incomes-source-sumary', IncomeSourceSumary.as_view(), name="incomes-source-sumary"),
]
