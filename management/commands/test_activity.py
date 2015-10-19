# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.db import transaction

from openvpnmon.ewonconfig.models import EwonConfig, Chamber, Company
from openvpnmon.base.models import Client
from openvpnmon.ewonconfig import progress
from openvpnmon.activity.models import ActivityRegistry
from openvpnmon.exceptions import NoActiveJobError, MultipleActiveJobError

import threading, time, logging

log = logging.getLogger(__name__)

#--------------------------------------------------------------------------------

class FakeEwonConfig(object):
    def __init__(self, host='10.0.0.53', user='adm', pw='adm'):

        self.host = host
        self.user = user
        self.pw = pw
        self.__ftp = None
        self.pk = 1

    @property
    def urn(self):
        return u"%s-%s" % (
            self.__class__.__name__.lower(),
            self.pk
        )

    def _open_ftp_connection(self):
        return ftplib.FTP(self.host, self.user, self.pw)
    
    @property
    def base_config_path(self):
        return os.path.join(settings.BOARD_CONFIG_DIR, "ACS-TEST-1")

    @property
    def cfg_path(self):
        return os.path.join(self.base_config_path, "config.txt")
        
    @property
    def comcfg_path(self):
        return os.path.join(self.base_config_path, "comcfg.txt")
        
    
#--------------------------------------------------------------------------------


class Command(BaseCommand):
    args = ""
    help = "Testa l'esecuzione di un thread"

    @property
    def activityregistry(self):

        try:
            
            ar = ActivityRegistry.objects.get(
                reference = self.reference,
                consumed = False
            )
        except ActivityRegistry.DoesNotExist:

            raise NoActiveJobError("No active job for %s" % self.reference)
        except ActivityRegistry.MultipleObjectsReturned:

            raise MultipleActiveJobError("Multiple active jobs for %s" % self.reference)

        return ar

    def handle(self, *args, **options):

        try:
            worker_name = args[0]
        except IndexError:
            worker_name = "FakeWorker"

        try:
            host = args[1]
        except IndexError:
            host = "10.0.0.53"

        timeout = 5

        ewoncfg = FakeEwonConfig(host=host)
        self.reference = ewoncfg.urn

        progress.start_subthread(
            getattr(progress, worker_name),
            obj=ewoncfg,
            timeout=timeout
        )

        c = 10
        while True:

            ar = self.activityregistry
            prog_d = ar.as_dict()
            print("PROGRESS INFO: %s --> as_dict: %s" % (ar, prog_d))
            # Qui avviene una corretta impostazione del timeout,

            if prog_d['is_timed_out']:
                print("TIMEOUT")
                break
            elif prog_d['percent'] >= 100:
                print("raggiunta percentuale di 100")
                break

            c -= 1
            time.sleep(1)

            if c < 0:
                break

        ar = self.activityregistry
        ar.consumed = True
        ar.save()

