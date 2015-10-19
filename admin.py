
from openvpnmon.activity.models import ActivityRegistry
from django.contrib import admin
from django.utils.translation import ugettext, ugettext_lazy as _


class ActivityRegistryAdmin(admin.ModelAdmin):
    list_display = ('label', 'reference', 
        'start_time', 'end', 'done', 'msg', 
        'return_code', 'last_update_time', 
        'is_active', 'consumed'
    )
    list_filter = ('label', 'reference',)
    search_fields = ('reference',)
    actions = ['set_consumed']

    def set_consumed(self, request, queryset):
        for obj in queryset.all():
            obj.consumed = True
            obj.save()
    set_consumed.short_description = _("Set consumed")

admin.site.register(ActivityRegistry, ActivityRegistryAdmin)
