from django.urls import path
from .views import ServiceListCreateView, CreativeProfileCreateUpdateView, PortfolioCreateView

urlpatterns = [
    path("services/", ServiceListCreateView.as_view()),
    path("profile/", CreativeProfileCreateUpdateView.as_view()),  
    path("portfolio/", PortfolioCreateView.as_view()),
]

