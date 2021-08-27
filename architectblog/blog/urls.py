from django.urls import path
from .views import (
    IndexListView,
    EntryDetailView,
    EntryYearArchiveView,
    EntryMonthArchiveView,
    EntryDayArchiveView,
    EntrySearchView,
    TagArchiveView,
    LinkDetailView,
    QuoteDetailView,
    ArchiveView,
)

app_name = "blog"
urlpatterns = [
    path("", IndexListView.as_view(), name="home"),
    path(
        "<int:year>/<int:month>/<int:day>/<str:slug>/",
        EntryDetailView.as_view(month_format="%m"),
        name="entry_detail",
    ),
    path("<int:year>/", EntryYearArchiveView.as_view(), name="entry_archive_year"),
    path(
        "<int:year>/<int:month>/",
        EntryMonthArchiveView.as_view(month_format="%m"),
        name="entry_archive_month",
    ),
    path(
        "<int:year>/<int:month>/<int:day>/",
        EntryDayArchiveView.as_view(month_format="%m"),
        name="entry_archive_day",
    ),
    path("search/", EntrySearchView.as_view(), name="search"),
    path("tags/<tags>/", TagArchiveView.as_view(), name="tag_detail"),
    path(
        "links/<int:year>/<int:month>/<int:day>/<str:slug>/",
        LinkDetailView.as_view(month_format="%m"),
        name="link_detail",
    ),
    path(
        "quotes/<int:year>/<int:month>/<int:day>/<str:slug>/",
        QuoteDetailView.as_view(month_format="%m"),
        name="quote_detail",
    ),
    path("archive/", ArchiveView.as_view(), name="archive_view"),
]
