from django.contrib import admin
from .models import Service, CreativeProfile, PortfolioItem, RatingSuggestion

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")

class PortfolioInline(admin.TabularInline):
    model = PortfolioItem
    extra = 0

@admin.register(CreativeProfile)
class CreativeProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "location", "years_experience", "approved_stars", "is_active", "created_at")
    list_filter = ("is_active", "services")
    search_fields = ("display_name", "bio", "location")
    inlines = [PortfolioInline]

@admin.register(RatingSuggestion)
class RatingSuggestionAdmin(admin.ModelAdmin):
    list_display = ("profile", "suggested_stars", "confidence", "status", "reviewed_by", "reviewed_at", "created_at")
    list_filter = ("status",)
    search_fields = ("profile__display_name",)