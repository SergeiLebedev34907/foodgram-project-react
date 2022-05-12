from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name", "email")
    list_filter = ("first_name",)
    search_fields = ("email", "username")


admin.site.register(User, UserAdmin)
