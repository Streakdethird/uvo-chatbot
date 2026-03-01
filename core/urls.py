from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse



def home(request):
    return JsonResponse({"message": "UVO AI Backend is running 🚀"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/creatives/", include("creatives.urls")),
    path("api/", include("discovery.urls")),
    path("", home),
]