from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True)
    chat_id = models.CharField(max_length=20, blank=True, null=True)  # Telegram chat_id uchun

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Telefon raqamni normalizatsiya qilish
        self.phone_number = self.normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_phone_number(phone_number):
        phone_number = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if phone_number.startswith("998"):  # Agar xalqaro kodsiz kelgan bo'lsa
            phone_number = "+" + phone_number
        elif not phone_number.startswith("+998"):  # Agar boshqa formatda kelsa
            phone_number = "+998" + phone_number
        return phone_number

    @classmethod
    def register_or_update(cls, phone_number, chat_id):
        # Foydalanuvchi telefon raqami bilan ro'yxatdan o'tganmi yoki yo'qligini tekshiramiz
        try:
            company = cls.objects.get(phone_number=phone_number)
            if company.chat_id is not None:
                # Agar telefon raqami allaqachon ro'yxatdan o'tgan bo'lsa
                raise ValueError(f"Bu telefon raqami {phone_number} bilan ro'yxatdan o'tgan.")
            company.chat_id = chat_id
            company.save()
            return company
        except cls.DoesNotExist:
            # Telefon raqami bazada mavjud bo'lmasa, yangi yozuv yaratish
            return cls.objects.create(phone_number=phone_number, chat_id=chat_id)
        except ValueError as e:
            # Agar ro'yxatdan o'tgan bo'lsa, xatolikni qaytarish
            raise e



class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=255)
    count = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.count
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class CompanyList(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='company_list')

    def __str__(self):
        return f"Список компаний для {self.company.name}"
