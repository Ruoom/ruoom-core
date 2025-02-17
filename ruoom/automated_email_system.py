from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
from django.template.loader import render_to_string
from django.http import JsonResponse
from security.key_lock import RuoomSecurity
from administration.models import StudioSettings


def automated_email_send(recipient_email,subject,text_content,business_id=None):
    print("Sending email to "+str(recipient_email)+" for "+str(subject))

    from_email = ""
    if business_id:
        ruoom_security = RuoomSecurity()
        studio_obj = StudioSettings.objects.filter(business_id=business_id).first()
        if studio_obj.email_address and studio_obj.host_address and studio_obj.application_password and studio_obj.host_address and studio_obj.host_tls:
            from_email= studio_obj.email_address
            application_password = ruoom_security.decrypt_message(encrypted_message=studio_obj.application_password)
            backend = EmailBackend(host=studio_obj.host_address, port=studio_obj.host_port, username=studio_obj.email_address, 
                       password=application_password, use_tls=studio_obj.host_tls, fail_silently=False)
    
    if not from_email:  #Default to Ruoom credentials
        backend = EmailBackend(host=settings.EMAIL_HOST, port=settings.EMAIL_PORT, username=settings.EMAIL_HOST_USER, 
                       password=settings.EMAIL_HOST_PASSWORD, use_tls=settings.EMAIL_USE_TLS, fail_silently=False)
        from_email= settings.EMAIL_HOST_USER

    subject = subject
    text_content = text_content
    html_content = '<p style="font-size:30px;color:red;">'+text_content+'</p>'

    msg = EmailMultiAlternatives(subject, text_content, from_email,recipient_email,connection=backend)   
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    return JsonResponse({"message":"success"})


