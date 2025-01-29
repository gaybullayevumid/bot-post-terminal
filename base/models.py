from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True)
    tg_id = models.CharField(max_length=20, blank=True, null=True)  # Telegram foydalanuvchi ID-si uchun
    chat_id = models.CharField(max_length=20, blank=True, null=True)  # Telegram chat ID-si uchun

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.phone_number = self.normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_phone_number(phone_number):
        phone_number = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if phone_number.startswith("998"):
            phone_number = "+" + phone_number
        elif not phone_number.startswith("+998"):
            phone_number = "+998" + phone_number
        return phone_number

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=255)
    count = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.count
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
