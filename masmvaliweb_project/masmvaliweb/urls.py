from django.conf.urls import patterns, url

from masmvaliweb import views

urlpatterns = patterns('masmvaliweb.views',
    url(r'^$', views.index, name='index'),
    url(r'^assembly/add$', views.add_assembly, name='add_assembly'),
    url(r'^assembly/add/success$', views.add_assembly_success, name='add_assembly_success'),
    url(r'^browse$', views.browse, name='browse'),
    url(r'^browse/metagenome/(\d+)/$', views.metagenome, name='metagenome'),
)
