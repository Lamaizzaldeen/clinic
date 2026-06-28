from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.template.loader import render_to_string
from .models import Inquiry


def _update_inquiry_status(inquiry: Inquiry, reply_text: str) -> Inquiry:
    inquiry.reply = reply_text
    inquiry.replied_at = timezone.now()
    inquiry.is_read = True
    inquiry.save()
    return inquiry


def _send_reply_email(inquiry: Inquiry, reply_text: str, subject_title: str) -> None:
    context = {
        'subject_title': subject_title,
        'name': inquiry.name,
        'email': inquiry.email,
        'message': inquiry.message,
        'reply': reply_text,
        'created_at': inquiry.created_at,
    }
    html_message = render_to_string('contact/email_response.html', context)

    plain_message = (
        f"عزيزنا/عزيزتنا {inquiry.name}،\n\n"
        f"نشكرك على تواصلك معنا. لقد تم الرد على استفسارك على النحو التالي:\n\n"
        f"{reply_text}\n\n"
        f"---\n"
        f"تفاصيل الاستفسار الأصلي:\n"
        f"الاسم: {inquiry.name}\n"
        f"البريد الإلكتروني: {inquiry.email}\n"
        f"الرسالة: {inquiry.message}\n"
    )

    send_mail(
        subject=subject_title,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[inquiry.email],
        html_message=html_message,
        fail_silently=False,
    )


def reply_to_inquiry(inquiry: Inquiry, reply: str, subject_title: str) -> Inquiry:
    with transaction.atomic():
        inquiry = _update_inquiry_status(inquiry, reply)
        transaction.on_commit(lambda: _send_reply_email(inquiry, reply, subject_title))
    return inquiry
