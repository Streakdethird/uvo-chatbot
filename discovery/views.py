from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from creatives.models import CreativeProfile, Service
from creatives.serializers import CreativeProfileSerializer

class SearchCreativesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        service_slug = request.query_params.get("service")
        if not service_slug:
            return Response({"error": "Provide ?service=service-slug"}, status=400)

        # Filter by service
        qs = CreativeProfile.objects.filter(is_active=True, services__slug=service_slug).distinct()

        # Simple ranking: approved_stars first, then experience
        qs = qs.order_by("-approved_stars", "-years_experience", "-created_at")

        data = CreativeProfileSerializer(qs, many=True).data
        return Response({"results": data})