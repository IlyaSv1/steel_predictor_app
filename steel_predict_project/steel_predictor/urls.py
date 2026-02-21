from django.urls import path, register_converter
from . import views


class SteelTypeConverter:
    regex = "carbon|stainless"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(SteelTypeConverter, "steel")

app_name = "steel_predictor"

urlpatterns = [
    path("", views.index, name="index"),
    path("predict/<steel:steel_type>/", views.predict_view, name="predict"),
    path("history/<steel:steel_type>/", views.history_view, name="history"),
    path(
        "history/<steel:steel_type>/delete/<int:pk>/",
        views.delete_prediction,
        name="delete_prediction",
    ),
]
