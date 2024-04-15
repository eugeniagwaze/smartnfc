from django.contrib import admin
from .models import *

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    pass

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    pass

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    pass

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    pass

@admin.register(PaynowPayment)
class PaynowPaymentAdmin(admin.ModelAdmin):
    pass

@admin.register(Withdraw)
class WithdrawAdmin(admin.ModelAdmin):
    pass

@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    pass

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    pass