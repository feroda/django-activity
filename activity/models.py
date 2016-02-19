# -*- coding: utf-8 -*-

# Copyright Luca Ferroni @2009
# License AGPLv3

from django.db import models

import time, logging

log = logging.getLogger(__name__)


#---------------------------------------------------------------------

class ActivityRegistry(models.Model):

    # Label is a generic label for the activity
    # Can be thread identifier, or kind of job, ...
    label = models.CharField(max_length=512)

    # Reference is an identifier to be used for
    # object or objects bound to this activity
    reference = models.CharField(max_length=512, null=True)

    start_time = models.PositiveIntegerField(null=True, 
        default=None
    )

    # End and done are relative info
    end = models.PositiveIntegerField(default=100)
    done = models.PositiveIntegerField(default=0)

    # Timeout is expressed in seconds. And it is to be
    # intended "seconds from start_time"
    timeout = models.PositiveIntegerField(null=True)

    msg = models.TextField(default=u"nessun aggiornamento in corso")
    # Può essere nullo quando lo slot è creato, ma non si è ancora fatto "set_start"
    last_update_time = models.PositiveIntegerField(null=True)

    is_locked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    consumed = models.BooleanField(default=False)

    return_code = models.CharField(max_length=512, 
        default='', blank=True
    )
    note = models.TextField(default='', blank=True)
    
    RETURN_STARTED = "STARTED"
    RETURN_DONE = "DONE"
    RETURN_TIMEOUT = "TIMEOUT"
    RETURN_PERMISSIONDENIED = "PERMISSIONDENIED"
    RETURN_STOPPED = "STOPPED"

    class Meta:
        get_latest_by = "last_update_time"

    def __unicode__(self):
        return u"""reference=%s, label=%s, start_time=%s, end=%s, \
done=%s, timeout=%s, consumed=%s, msg=%s, \
last_update_time=%s, is_locked=%s, is_active=%s, return_code=%s""" % (
            self.reference, self.label, self.start_time, self.end, self.done,
            self.timeout, self.consumed, self.msg, self.last_update_time, self.is_locked,
            self.is_active, self.return_code
            )

    def clean(self):
        if self.reference == "":
            self.reference = None

    def save(self, *args, **kw):
        self.clean()
        super(ActivityRegistry, self).save(*args, **kw)

    def set_start(self, timeout, end=100, msg=""):
        """Facility to start an activity."""

        if (timeout < end): 
            log.debug("Attenzione: hai impostato timeout %s < end %s" % (timeout, end))

        if self.is_locked:
                log.debug("Non e' possibile far partire un altro processo")
                raise AlreadyRunningError("Esiste già un thread in esecuzione per questa attività, non è possibile avviarne un altro.")
                #return False

        self.start_time = time.time()
        self.timeout = timeout #secs
        self.msg = msg
        self.end = end
        self.is_locked = True
        self.is_active = True

        self.last_update_time = self.start_time
        self.done = 0
        self.return_code = ActivityRegistry.RETURN_STARTED
        self.save()
        log.debug("Creato registro attivita': %s" % self)
        return True

    @property
    def eta(self):
        if not self.is_running():
            return 0
        #log.debug("CALCOLO ETA: timeout=%s start_time=%s label=%s" % (self.timeout, self.start_time, self.label))
        return (self.timeout or 0) - (time.time() - (self.start_time or 0))

    def progress(self):
        log.debug(u"PROGRESS: done=%s end=%s, eta=%s" % (self.done, self.end, self.eta))
        return self.done*100/self.end
    
    def is_done(self):
        return self.done == self.end

    def touch(self, msg, return_code=None, note=""):
        """Update timestamp and message."""

        self.last_update_time = time.time()
        self.msg = msg
        if return_code:    
            self.return_code = return_code
        self.note = note
        self.save()
    
    def inc(self, value, msg, note=""):
        """Increment completing percent and set message."""

        log.debug("incremento done=%s + %s" % (self.done, value))
        self.done += value
        if self.done == self.end:
            self.set_done(msg=msg, note=note)
        else:
            self.last_update_time = time.time()
            self.msg = msg
            self.note = note
            self.return_code = "INC"
            self.save()
        
    def set_done(self, msg=None, note=""):
        """Finish an activity"""

        log.debug(u"PROGRESS entering set done...")
        self.done = self.end
        if msg:
            self.msg = msg
        self.note=note
        self.is_locked = False
        self.is_active = False
        self.last_update_time = time.time()
        self.return_code = ActivityRegistry.RETURN_DONE
        log.debug(u"PROGRESS set done: %s" % self.as_dict())
        self.save()

    def is_timed_out(self):
        """Tell if an activity has timed out."""

        return self.return_code == ActivityRegistry.RETURN_TIMEOUT

    def set_timeout(self):
        """Explicitly set timeout for an activity."""

        self.return_code = ActivityRegistry.RETURN_TIMEOUT
        self.is_locked = False
        self.is_active = False
        self.last_update_time = time.time()
        self.msg = u"L'attività è andata in timeout. Ultimo messaggio: %s" % self.msg
        self.save()

    def is_running(self):
        """Tell if an activity is running."""

        if self.return_code in [
            ActivityRegistry.RETURN_PERMISSIONDENIED,
            ActivityRegistry.RETURN_STOPPED
        ]:
            return False
        if (self.done >= self.end):
            return False
        else:
            if self.last_update_time == self.start_time:
                return True
            else:
                return bool(self.timeout - (time.time() - self.start_time))
                #return (time.time() - self.last_update_time) > MAXIMUM_ETA_UPDATE_TOLERANCE
        
    def as_dict(self):
        """Return in serializable dict."""

        return {
            'percent' : self.progress(),
            'msg' : self.msg,
            'eta' : self.eta,
            'is_timed_out' : self.is_timed_out(),
            'is_running' : self.is_running(),
            'last_update_time' : self.last_update_time,
            'return_code' : self.return_code,
        }

#--------------------------------------------------------------------------------

class ActiveJob(models.Model):
    """This model is used to keep track of active jobs"""

    # Reference is an identifier to be used for
    # object or objects bound to this activity
    reference = models.CharField(max_length=512, unique=True)

    activity = models.OneToOneField(ActivityRegistry)
    
