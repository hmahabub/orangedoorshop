from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from . import views  # Import the views we just created

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inventory/', include('inventory.urls')),
    path('pos/', include('pos.urls')),
    path('reports/', include('reports.urls')),
    path('', views.dashboard, name='dashboard'),  # Main index page
    path('dashboard/', views.dashboard, name='dashboard'),  # Main dashboard
]