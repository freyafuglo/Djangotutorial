from django.urls import path

from . import views

app_name = "polls"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
    path("<int:question_id>/export/", views.export_excel, name="export_excel"),
    path("create/", views.CreateView.as_view(), name="create"),
    path("search/", views.get_name, name="search"),

    path("piechart-test/", views.piechart_test, name="piechart_test"),
    path("barchart-test/", views.barchart_test, name="barchart_test"),
    
]