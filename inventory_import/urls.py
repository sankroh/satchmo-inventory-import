from django.conf.urls.defaults import *

urlpatterns = patterns('inventory_import.views',
    url(r'^upload/$', 'upload', {}, 'admin_inventory_import'),
)
