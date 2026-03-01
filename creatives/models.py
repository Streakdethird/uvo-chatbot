from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Service(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)

    def __str__(self):
        return self.name

class CreativeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="creative_profile")
    display_name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=120, blank=True)
    min_price = models.PositiveIntegerField(null=True, blank=True)  # in naira
    max_price = models.PositiveIntegerField(null=True, blank=True)  # in naira
    
# flexible tags: genres, event types, styles, specialties
    tags = models.JSONField(default=dict, blank=True)  # e.g. {"genres":["afrobeats"],"events":["wedding"]}
    
    instagram = models.CharField(max_length=120, blank=True)
    twitter = models.CharField(max_length=120, blank=True)
    tiktok = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)

    services = models.ManyToManyField(Service, related_name="creatives", blank=True)

    # Public rating ONLY after you approve
    approved_stars = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    approved_rating_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

class PortfolioItem(models.Model):
    profile = models.ForeignKey(CreativeProfile, on_delete=models.CASCADE, related_name="portfolio_items")
    title = models.CharField(max_length=120)
    url = models.URLField()
    kind = models.CharField(
        max_length=30,
        choices=[
            ("image", "Image"),
            ("video", "Video"),
            ("design", "Design"),
            ("code", "Code"),
            ("music", "Music"),
            ("writing", "Writing"),
            ("other", "Other"),
        ],
        default="other",
    )
    created_at = models.DateTimeField(auto_now_add=True)

class RatingSuggestion(models.Model):
    """
    AI suggestion (not public) → you approve/adjust.
    """
    profile = models.OneToOneField(CreativeProfile, on_delete=models.CASCADE, related_name="rating_suggestion")
    suggested_stars = models.DecimalField(max_digits=2, decimal_places=1)  # 0.0 - 5.0
    confidence = models.DecimalField(max_digits=3, decimal_places=2, default=0.50)  # 0.00 - 1.00
    explanation = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
    )
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_ratings")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)