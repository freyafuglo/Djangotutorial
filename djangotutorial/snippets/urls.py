from django.urls import include, path
from rest_framework.routers import DefaultRouter
from snippets import views

app_name = "snippets"

router = DefaultRouter()
router.register(r"", views.SnippetViewSet, basename="snippet")
router.register(r"users", views.UserViewSet, basename="user")

urlpatterns = [
    path("root", views.api_root, name="root"),
    path("", include(router.urls)),
]