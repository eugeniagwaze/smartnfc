from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Wallet(models.Model):
    account_name = models.CharField(max_length=8, unique=True, blank=True)
    currency = models.CharField(max_length=50, blank=True)
    date_added = models.DateField(auto_now_add=True)
    dual_account = models.CharField(max_length=50, unique=False, blank=True)
    amount_zig = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    cell_number = models.CharField(max_length=15, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_wallets', blank=True)
    date = models.DateField(default=timezone.now, blank=True)

    def save(self, *args, **kwargs):
        if not self.account_name:
            # Logic to generate account name
            pass
        if not self.dual_account:
            # Logic to generate dual account
            pass
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.account_name


class Deposit(models.Model):
    date = models.DateField(default=timezone.now, blank=True)
    trans_id = models.CharField(max_length=50, unique=True, blank=True)
    amount_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    currency = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='deposits', blank=True)

    def save(self, *args, **kwargs):
        if not self.trans_id:
            # Logic to generate transaction ID
            pass
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.trans_id




class Withdraw(models.Model):
    date = models.DateField(default=timezone.now, blank=True)
    trans_id = models.CharField(max_length=50, unique=True, blank=True)
    amount_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    currency = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdraw', blank=True)

    def save(self, *args, **kwargs):
        if not self.trans_id:
            # Logic to generate transaction ID
            pass
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.trans_id

class Payment(models.Model):
    date = models.DateField(default=timezone.now, blank=True)
    trans_id = models.CharField(max_length=50, unique=True, blank=True)
    amount_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    currency = models.CharField(max_length=50, blank=True)
    receiver = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='payment', blank=True)

    def save(self, *args, **kwargs):
        if not self.trans_id:
            # Logic to generate transaction ID
            pass
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.trans_id

class Credit(models.Model):
    date = models.DateField(default=timezone.now, blank=True)
    trans_id = models.CharField(max_length=50, unique=True, blank=True)
    amount_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    currency = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='credit', blank=True)

    def save(self, *args, **kwargs):
        if not self.trans_id:
            # Logic to generate transaction ID
            pass
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.trans_id


class Transaction(models.Model):
    TRANSACTION_CHOICES = (
        ('withdrawal', 'Withdrawal'),
        ('deposit', 'Deposit'),
        ('payment', 'Payment'),
        ('credit', 'Credit'),
    )
    date = models.DateField(default=timezone.now, blank=True)
    comment = models.TextField(blank=True)
    trans_id = models.CharField(max_length=50, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    currency = models.CharField(max_length=50, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_CHOICES, blank=True)
    status = models.CharField(max_length=20,blank=True)

    def save(self, *args, **kwargs):
        if not self.trans_id:
            # Logic to generate transaction ID
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.trans_id


class Account(models.Model):
    full_name = models.CharField(max_length=100, blank=True)
    username = models.CharField(max_length=50, unique=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)
    documents = models.FileField(upload_to='documents/', blank=True)
    approval_status = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name


class PaynowPayment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cellphone = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    reference = models.CharField(max_length=100)
    paynow_reference = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    details = models.CharField(max_length=500, blank=True)

    init_status = models.CharField(max_length=10, blank=True)
    poll_url = models.CharField(max_length=500,blank=True)
    browser_url = models.CharField(max_length=500,blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10)
    paid = models.BooleanField(default=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username + ' - $' + str(self.amount) + ' - ' + self.status
