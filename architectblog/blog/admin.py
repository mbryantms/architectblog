from django.contrib import admin
from .models import Entry, Tag, Quotation, Blogmark, Series
from django.db.models.functions import Length


class BaseAdmin(admin.ModelAdmin):
    date_hierarchy = "created_time"
    raw_id_fields = ("tags",)
    list_display = ("__str__", "slug", "created_time", "tag_summary")
    autocomplete_fields = ("tags",)
    exclude = ["search_document"]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    date_hierarchy = "created_time"
    list_display = ("__str__", "slug", "created_time", "status")
    autocomplete_fields = ("tags",)
    exclude = ["search_document"]
    search_fields = ("tags__tag", "title", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["metadata"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "title",
                    "slug",
                    "tags",
                    "created_time",
                    "author",
                    "status",
                    "series",
                    "content",
                ]
            },
        ),
        (
            "Advanced",
            {
                "classes": ("collapse",),
                "fields": [
                    ("longitude", "latitude"),
                    "metadata",
                    "views",
                ],
            },
        ),
    ]


@admin.register(Quotation)
class QuotationAdmin(BaseAdmin):
    search_fields = ("tags__tag", "quotation")
    prepopulated_fields = {"slug": ("source",)}


@admin.register(Blogmark)
class BlogmarkAdmin(BaseAdmin):
    search_fields = ("tags__tag", "commentary")
    prepopulated_fields = {"slug": ("link_title",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("tag",)
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "tag",
                ]
            },
        ),
    ]

    def get_search_results(self, request, queryset, search_term):
        search_term = search_term.strip()
        if search_term:
            return (
                queryset.filter(tag__icontains=search_term)
                .annotate(tag_length=Length("tag"))
                .order_by("tag_length"),
                False,
            )
        else:
            return queryset.none(), False


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
