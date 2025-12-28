from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Course)
admin.site.register(models.Resource)
admin.site.register(models.Thread)
admin.site.register(models.Tag)
admin.site.register(models.Category)
admin.site.register(models.Reply)
admin.site.register(models.Report)
