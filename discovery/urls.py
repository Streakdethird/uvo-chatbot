from django.urls import path
from .views import SearchCreativesView
from .ratings_views import SuggestRatingView, ApproveRatingView
from .chat_views import ChatView

urlpatterns = [
    path("search/", SearchCreativesView.as_view()),
    path("ratings/suggest/", SuggestRatingView.as_view()),
    path("ratings/approve/", ApproveRatingView.as_view()),
    path("chat/", ChatView.as_view()),
]