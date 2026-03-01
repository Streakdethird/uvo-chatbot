from rest_framework import serializers
from .models import CreativeProfile, Service, PortfolioItem, RatingSuggestion
from django.contrib.auth import get_user_model

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "slug"]

class PortfolioItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioItem
        fields = ["id", "title", "url", "kind", "created_at"]
        read_only_fields = ["id", "created_at"]

class CreativeProfileSerializer(serializers.ModelSerializer):
    services = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Service.objects.all(), required=False
    )
    portfolio_items = PortfolioItemSerializer(many=True, read_only=True)

    class Meta:
        model = CreativeProfile
        fields = [
            "id",
            "display_name",
            "bio",
            "years_experience",
            "location",
            "instagram",
            "twitter",
            "tiktok",
            "website",
            "services",
            "approved_stars",
            "approved_rating_count",
            "is_active",
            "created_at",
            "portfolio_items",
            "min_price",
            "max_price",
            "tags",
        ]
        read_only_fields = ["id", "approved_stars", "approved_rating_count", "created_at"]

class RatingSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatingSuggestion
        fields = ["suggested_stars", "confidence", "explanation", "status", "created_at"]
        read_only_fields = ["status", "created_at"]

User = get_user_model()

class CreativeProfileCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=120)
    bio = serializers.CharField(required=False, allow_blank=True)
    years_experience = serializers.IntegerField(required=False, min_value=0)
    location = serializers.CharField(required=False, allow_blank=True)
    min_price = serializers.IntegerField(required=False, min_value=0)
    max_price = serializers.IntegerField(required=False, min_value=0)
    tags = serializers.DictField(required=False)

    instagram = serializers.CharField(required=False, allow_blank=True)
    twitter = serializers.CharField(required=False, allow_blank=True)
    tiktok = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)

    services = serializers.ListField(child=serializers.CharField(), required=False)

    def create(self, validated_data):
        email = validated_data.pop("email")
        services = validated_data.pop("services", [])

        user, _ = User.objects.get_or_create(username=email, defaults={"email": email})

        profile, _ = CreativeProfile.objects.get_or_create(
            user=user,
            defaults={"display_name": validated_data.get("display_name", "Unnamed")}
        )

        # update fields
        for k, v in validated_data.items():
            setattr(profile, k, v)
        profile.save()

        if services:
            profile.services.set(Service.objects.filter(slug__in=services))

        return profile
