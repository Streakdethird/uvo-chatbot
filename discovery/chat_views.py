# discovery/chat_views.py
from django.db import models

import re
from django.utils.text import slugify
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from creatives.models import CreativeProfile, Service
from creatives.serializers import CreativeProfileSerializer


# --- helpers ---
MONEY_RE = re.compile(r"(?:₦|ngn|naira)?\s*([0-9]{1,3}(?:[,0-9]{0,3})*)(k)?", re.IGNORECASE)

def normalize_money(text: str) -> int | None:
    """
    Parses amounts like:
    - 50k -> 50000
    - ₦100,000 -> 100000
    - 120000 -> 120000
    Returns integer naira amount.
    """
    if not text:
        return None
    m = MONEY_RE.search(text.replace(" ", ""))
    if not m:
        return None
    num = int(m.group(1).replace(",", ""))
    if m.group(2):  # 'k'
        num *= 1000
    return num

def extract_budget(message: str) -> dict:
    """
    Extracts:
    - max_budget: "under 50k", "below 100k"
    - min_budget: "from 50k"
    - range: "50k-150k"
    """
    m = (message or "").lower()

    # range like 50k-150k
    range_match = re.search(r"([0-9,]+k?)\s*(?:-|to)\s*([0-9,]+k?)", m)
    if range_match:
        lo = normalize_money(range_match.group(1))
        hi = normalize_money(range_match.group(2))
        return {"min_budget": lo, "max_budget": hi}

    # under/below/max
    if any(w in m for w in ["under", "below", "max"]):
        amt = normalize_money(m)
        if amt:
            return {"min_budget": None, "max_budget": amt}

    # from/at least/min
    if any(w in m for w in ["from", "at least", "minimum", "min"]):
        amt = normalize_money(m)
        if amt:
            return {"min_budget": amt, "max_budget": None}

    return {"min_budget": None, "max_budget": None}

def extract_location(message: str) -> str | None:
    """
    Quick MVP:
    - looks for 'in/around/within <place>' pattern
    - uses a small allowlist you can expand
    """
    m = (message or "").lower()

    cities = [
        "lagos", "abuja", "ibadan", "port harcourt", "ph", "benin", "enugu", "ilorin",
        "kaduna", "kano", "jos", "owerri", "abeokuta"
    ]

    in_match = re.search(r"\b(in|around|within|at)\s+([a-z ]{3,25})\b", m)
    if in_match:
        candidate = in_match.group(2).strip()
        if candidate == "ph":
            return "Port Harcourt"
        for c in cities:
            if c in candidate:
                return "Port Harcourt" if c == "ph" else c.title()
        return candidate.title()

    for c in cities:
        if re.search(rf"\b{re.escape(c)}\b", m):
            return "Port Harcourt" if c == "ph" else c.title()

    return None

def extract_tags(message: str) -> dict:
    """
    Extracts genre + event type keywords (MVP).
    """
    m = (message or "").lower()

    genres = []
    for g in ["afrobeats", "amapiano", "hip hop", "r&b", "gospel", "drill", "house", "techno"]:
        if g in m:
            genres.append(g)

    events = []
    for e in ["wedding", "club", "birthday", "corporate", "party", "event"]:
        if e in m:
            events.append(e)

    return {"genres": genres, "events": events}

def detect_service_slug(message: str) -> str | None:
    """
    Intent detection:
    - keyword rules (fast + controllable)
    - fallback to existing Service names/slugs
    """
    m = (message or "").lower()

    rules = [
        (["logo", "brand identity", "branding"], "logo-design"),
        (["video", "editor", "edit", "capcut", "premiere", "after effects"], "video-editing"),
        (["photography", "photographer"], "photography"),
        (["ui", "ux", "product design"], "ui-ux-design"),
        (["web", "website", "frontend", "developer"], "web-development"),

        # music / entertainment
        (["dj", "deejay", "disc jockey"], "dj"),
        (["producer", "music producer", "production"], "music-production"),
        (["beat", "instrumental", "beatmaker"], "beat-making"),
        (["mix", "master", "mixing", "mastering"], "mixing-mastering"),
    ]

    for keywords, slug in rules:
        if any(k in m for k in keywords):
            return slug

    # fallback: match existing services by name/slug text
    for s in Service.objects.all():
        if s.name.lower() in m or s.slug.replace("-", " ") in m:
            return s.slug

    return None

def ensure_service_exists(service_slug: str) -> Service:
    """
    Auto-create a service if it doesn't exist.
    """
    service_slug = slugify(service_slug)
    service = Service.objects.filter(slug=service_slug).first()
    if service:
        return service

    # Better display names for acronyms
    if service_slug == "dj":
        name = "DJ"
    elif service_slug == "ui-ux-design":
        name = "UI/UX Design"
    else:
        name = service_slug.replace("-", " ").title()

    return Service.objects.create(name=name, slug=service_slug)


class ChatView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        message = request.data.get("message", "")
        if not message:
            return Response({"error": "message is required"}, status=400)

        service_slug = detect_service_slug(message)
        location = extract_location(message)
        budget = extract_budget(message)
        tags = extract_tags(message)

        if not service_slug:
            return Response({
                "reply": "What service do you need? Examples: logo design, video editing, DJ, music producer.",
                "service_slug": None,
                "filters": {"location": location, **budget, **tags},
                "results": []
            })

        # auto-create service if missing
        service = ensure_service_exists(service_slug)
        service_slug = service.slug

        qs = CreativeProfile.objects.filter(
            is_active=True,
            services__slug=service_slug
        ).distinct()

        # -------------------------
        # LOCATION FILTER
        # -------------------------
        if location:
            qs = qs.filter(location__icontains=location)

        # -------------------------
        # BUDGET FILTER (REAL)
        # -------------------------
        min_budget = budget.get("min_budget")
        max_budget = budget.get("max_budget")

        if max_budget is not None:
            qs = qs.filter(
                models.Q(min_price__lte=max_budget) |
                models.Q(min_price__isnull=True)
            )

        if min_budget is not None:
            qs = qs.filter(
                models.Q(max_price__gte=min_budget) |
                models.Q(max_price__isnull=True)
            )

        # -------------------------
        # TAG FILTER (GENRES / EVENTS)
        # -------------------------
        preferred = qs

        # genre match
        for g in tags["genres"]:
            preferred = preferred.filter(tags__genres__contains=[g])

        # event match
        for e in tags["events"]:
            preferred = preferred.filter(tags__events__contains=[e])

        if preferred.exists():
            qs = preferred

        # -------------------------
        # RANKING
        # -------------------------
        qs = qs.order_by("-approved_stars", "-years_experience", "-created_at")[:10]
        results = CreativeProfileSerializer(qs, many=True).data

        # -------------------------
        # RESPONSE BUILDING
        # -------------------------
        parts = [f"I searched for **{service_slug.replace('-', ' ')}**"]

        if location:
            parts.append(f"in **{location}**")

        if max_budget:
            parts.append(f"with budget up to **₦{max_budget:,}**")

        if min_budget and not max_budget:
            parts.append(f"with budget from **₦{min_budget:,}**")

        if tags["genres"]:
            parts.append(f"(genre: {', '.join(tags['genres'])})")

        if tags["events"]:
            parts.append(f"(event: {', '.join(tags['events'])})")

        if not results:
            return Response({
                "reply": " ".join(parts) + " — but I didn’t find anyone yet. Try adjusting your filters.",
                "service_slug": service_slug,
                "filters": {"location": location, **budget, **tags},
                "results": []
            })

        top = results[0]["display_name"]

        return Response({
            "reply": " ".join(parts) + f". I found **{len(results)}** creatives. Top match: **{top}**.",
            "service_slug": service_slug,
            "filters": {"location": location, **budget, **tags},
            "results": results
        })