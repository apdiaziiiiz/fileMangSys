"""
Root URL configuration for fileMangSys project.
Includes prototype routes for Part 1 UI design.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin-django/', admin.site.urls),
    path('', include('ui_prototype.urls')),
]
