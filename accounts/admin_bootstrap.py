from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

@csrf_exempt
def bootstrap_admin(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    token = request.headers.get("X-BOOTSTRAP-TOKEN", "")
    if not token or token != getattr(settings, "CREATE_ADMIN_TOKEN", ""):
        return JsonResponse({"error": "Forbidden"}, status=403)

    username = "admin"
    password = getattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", "")
    email = "admin@theuniformrepublic.com"

    if not password:
        return JsonResponse({"error": "BOOTSTRAP_ADMIN_PASSWORD not set"}, status=500)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"message": "Admin already exists"}, status=200)

    User.objects.create_superuser(username=username, email=email, password=password)
    return JsonResponse({"message": "Admin created"}, status=201)