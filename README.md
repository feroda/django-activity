# django-activity

Activity/Task (very ;)) simple tracker and state persistence for Django

## Usage

`pip install -e git://github.com/feroda/django-activity.git#egg=django_activity`

1. Add the `activity` app to `INSTALLED_APPS` in your Django `settings.py`
2. Apply migrations: `python manage.py migrate activity`
3. And then in your code:
   - When you receive a task to do, make an instance `ar = ActivityRegistry(label=your_label_for_the_job)` (`label` required)
   - To find instances to start filter them by `ActivityRegistry.objects.filter(start_time__isnull=True)`
   - Before activating the actual job do `ar.set_start(timeout=T, end=E)` (T must be > E, E = 100 by default)
   - If you have steps in your job you can do `ar.inc(N, msg='my n step done')`
   - When you finish the job you can do `ar.set_done(msg='my job is finished')` (msg is empty by default)
   - To check if it is done you can do `ar.is_done()`
   - To check if it is running you can do `ar.is_running()`

