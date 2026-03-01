from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser


from creatives.models import CreativeProfile, RatingSuggestion


class SuggestRatingView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        profile_id = request.data.get("profile_id")
        suggested_stars = request.data.get("suggested_stars")
        confidence = request.data.get("confidence", 0.50)
        explanation = request.data.get("explanation", "")

        if profile_id is None or suggested_stars is None:
            return Response({"error": "profile_id and suggested_stars are required"}, status=400)

        profile = get_object_or_404(CreativeProfile, id=profile_id)

        obj, _ = RatingSuggestion.objects.update_or_create(
            profile=profile,
            defaults={
                "suggested_stars": suggested_stars,
                "confidence": confidence,
                "explanation": explanation,
                "status": "pending",
                "reviewed_by": None,
                "reviewed_at": None,
            },
        )

        return Response({
            "message": "Rating suggestion saved (pending review).",
            "profile_id": profile.id,
            "suggested_stars": str(obj.suggested_stars),
            "confidence": str(obj.confidence),
            "status": obj.status
        })


class ApproveRatingView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        profile_id = request.data.get("profile_id")
        approved_stars = request.data.get("approved_stars")

        if profile_id is None or approved_stars is None:
            return Response({"error": "profile_id and approved_stars are required"}, status=400)

        profile = get_object_or_404(CreativeProfile, id=profile_id)
        suggestion = get_object_or_404(RatingSuggestion, profile=profile)

        profile.approved_stars = approved_stars
        profile.save(update_fields=["approved_stars"])

        suggestion.status = "approved"
        suggestion.reviewed_at = timezone.now()
        suggestion.save(update_fields=["status", "reviewed_at"])

        return Response({
            "message": "Approved rating saved.",
            "profile_id": profile.id,
            "approved_stars": str(profile.approved_stars)
        })