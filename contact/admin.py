from django.contrib import admin
from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'email', 'is_read', 'replied_at', 'created_at']
    list_filter = ['is_read']
    search_fields = ['name', 'email', 'subject']
    ordering = ['is_read', '-created_at']
    readonly_fields = ['replied_at']
