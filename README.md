# django-activity
Activity/Task simple tracker and state persistence for Django

Just clone or add as submodule in your project and link "activity" app directory
in your Django project.
Then add it to your INSTALLED_APPS

If your Django project is called ''djproject''
you could install the actvity app with:

  $ cd djproject
  $ git submodule add https://github.com/feroda/django-activity.git
  $ ln -s django-activity/activity activity
  $ add the activity app to INSTALLED_APPS in djproject/settings.py


