from django.db import models
from django.utils import timezone
from inventory.models import Product
from pos.models import Sale

class StockValuationReport(models.Model):
    generated_at = models.DateTimeField(auto_now_add=True)
    total_valuation = models.DecimalField(max_digits=12, decimal_places=2)
    total_products = models.IntegerField()
    generated_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return f"Stock Valuation - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"

class ProfitLossReport(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2)
    generated_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return f"P&L Report {self.start_date} to {self.end_date}"