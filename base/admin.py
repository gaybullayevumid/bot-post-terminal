from django.contrib import admin
from .models import *


from django.contrib import admin
from .models import Company, Product

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1


class CompanyAdmin(admin.ModelAdmin):
    inlines = [ProductInline]

admin.site.register(Company, CompanyAdmin)

