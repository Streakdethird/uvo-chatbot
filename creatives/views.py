from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from .serializers import CreativeProfileCreateSerializer

from .models import CreativeProfile, Service, PortfolioItem
from .serializers import CreativeProfileSerializer, PortfolioItemSerializer, ServiceSerializer


class ServiceListCreateView(generics.ListCreateAPIView):
    queryset = Service.objects.all().order_by("name")
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        name = serializer.validated_data["name"]
        serializer.save(slug=slugify(name))


class MyCreativeProfileView(APIView):
    """
    Create/update the logged-in user's creative profile.
    For MVP, we allow unauth too (but better to add auth next).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # For now we fetch by ?user_id= (MVP)
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "Provide user_id"}, status=400)
        profile = get_object_or_404(CreativeProfile, user_id=user_id)
        return Response(CreativeProfileSerializer(profile).data)

    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"error": "Provide user_id"}, status=400)

        profile, _ = CreativeProfile.objects.get_or_create(
            user_id=user_id,
            defaults={"display_name": request.data.get("display_name", "Unnamed")},
        )

        serializer = CreativeProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)


class PortfolioCreateView(generics.CreateAPIView):
    serializer_class = PortfolioItemSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        profile_id = self.request.data.get("profile_id")
        profile = get_object_or_404(CreativeProfile, id=profile_id)
        serializer.save(profile=profile)



class CreativeProfileCreateUpdateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CreativeProfileCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(CreativeProfileSerializer(profile).data, status=200)