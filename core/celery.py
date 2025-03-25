# celery.py (inside Django project folder)
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create Celery app with result backend configuration
app = Celery('core', 
             broker='pyamqp://guest@localhost//', 
             backend='django-cache',
             pool='solo')  # Use 'solo' pool for Windows compatibility

# Load task modules from all registered Django apps
app.config_from_object('django.conf:settings', namespace='CELERY')

# Set broker connection retry on startup
app.conf.broker_connection_retry_on_startup = True

# Configure task result backend
app.conf.result_backend = 'django-cache'
app.conf.result_expires = 3600  # Results expire after 1 hour

# Auto-discover tasks in Django apps
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=False)
def debug_task(self):
    print(f'Request: {self.request!r}')
