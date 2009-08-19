from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
		(r'^services/$', 'webpages.views.service'),
		(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
			{'document_root': settings.STATIC}),
)
