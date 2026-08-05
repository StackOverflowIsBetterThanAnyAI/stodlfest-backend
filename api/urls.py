from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CreateUserView,
    GeminiChatView,
    JobViewSet,
    MemberViewSet,
    TaskViewSet,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"members", MemberViewSet, basename="member")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"chat", GeminiChatView, basename="chat")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", CreateUserView.as_view(), name="register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
