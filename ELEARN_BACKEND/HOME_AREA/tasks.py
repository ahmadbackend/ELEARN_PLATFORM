# the plan
"""
1) create send email and activation code done tested
2)create file and video uploader
3) routine emails to members about new courses 
4)schedule dleetion of activation codes from database done 

    """
import logging
from django.core.mail import send_mail
from celery import shared_task
from ELEARN_BACKEND import settings
from INSTRUCTOR.models import CODE_GENERATOR_INSTR
from STUDENT.models import CODE_GENERATOR
@shared_task(bind=True)
def send_email(self, target, message):
    logging.info(f"Starting send_email task for {target}")
    mail_subject = "Welcome on Board!"
    try:
        send_mail(
            subject=mail_subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[target],
            fail_silently=False,
        )
        logging.info(f"Email sent to {target}")
        return "Done"
    except Exception as e:
        logging.error(f"Failed to send email to {target}: {e}")
        raise e

@shared_task
def test_task():
    logging.info("Test task executed")
    return "Test completed"

@shared_task
def CleanDatabase(email, code,database):
    try:
        target = database.objects.get(EMAIL=email,ACTIVATION_CODE=code)
        target.delete()
        print ("deleted peacefully")
        return "DONE"
    except:
        return "mission failed"

@shared_task
def simple_task():
    print("Simple task executed")
    return "Done"