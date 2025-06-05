from django.contrib import admin
from .models import Category, Doctor, Appointment

# Register your models here.
admin.site.register(Category)
admin.site.register(Doctor)
admin.site.register(Appointment)



