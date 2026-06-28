from django.db import models


class Inquiry(models.Model):
    name = models.CharField(max_length=255, verbose_name='الاسم')
    email = models.EmailField(verbose_name='البريد الإلكتروني')
    subject = models.CharField(max_length=255, verbose_name='الموضوع')
    message = models.TextField(verbose_name='الرسالة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')

    is_read = models.BooleanField(default=False, verbose_name='مقروء')
    reply = models.TextField(blank=True, verbose_name='الرد')
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الرد')

    class Meta:
        db_table = 'inquiry'
        verbose_name = 'استفسار'
        verbose_name_plural = 'الاستفسارات'
        ordering = ['is_read', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"
