from django.contrib.auth.models import User
from django.http import JsonResponse
from django.conf import settings

def create_admin(request):
    secret = request.GET.get("secret")

    if secret != settings.SECRET_KEY:
        return JsonResponse({"error": "Not allowed"}, status=403)

    if User.objects.filter(username="admin").exists():
        return JsonResponse({"message": "Admin already exists"})

    User.objects.create_superuser(
        username="admin",
        email="admin@email.com",
        password="StrongPassword123!"
    )

    return JsonResponse({"message": "Admin created"})