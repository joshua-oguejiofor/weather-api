import asyncio
from app.celery_server.celery_instance import celery_app
from app.services.email_service import EmailService



email_service= EmailService()



    
@celery_app.task(bind= True, max_retries= 3, name= "email_verify_token_task", ignore_result= True)
def email_verify_token_task(self, email: str, token: str, first_name):
    try:
        asyncio.run(email_service.verify_email(
            to_email= email, first_name= first_name, 
            verify_link= token))
    except Exception as exc:
        raise self.retry(exc= exc, countdown= 60)



@celery_app.task(bind= True, max_retries= 3, name= "severe_weather_alert_task", ignore_result= True)
def send_severe_weather_alert_task(self, to_email: str, city: str, event: str, description: str, first_name: str):
    try:
        asyncio.run(email_service.send_severe_weather_alert(
            to_email= to_email, 
            first_name= first_name, 
            city= city, event= event, 
            description= description))
        
    except Exception as exc:
        raise self.retry(exc= exc, countdown= 60)
    
    
@celery_app.task(bind= True, max_retries= 3, name= "send_otp_task", ignore_result= True)
def send_otp_email_task(self, to_email: str, otp: str):
    try:
        asyncio.run(email_service.send_otp_email(
            to_email= to_email, otp= otp))
        
    except Exception as exc:
        raise self.retry(exc= exc, countdown= 60)
    
    
@celery_app.task(bind= True, max_retries= 3, name= "send_login_notification_task", ignore_result= True)
def send_login_notification_task(self, to_email: str, first_name: str, time: str):
    try:
        asyncio.run(email_service.send_login_notification(
            to_email= to_email,
            first_name= first_name, time= time))
        
    except Exception as exc:
        raise self.retry(exc= exc, countdown= 60)
