from django.views.generic.list import ListView
from django.views.generic.dates import (
    DateDetailView,
    YearArchiveView,
    MonthArchiveView,
    DayArchiveView,
)
from django.views.generic.base import TemplateView
from .models import Entry, Blogmark, Quotation, Tag, load_mixed_objects
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models import Count
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
import datetime
from django.http import Http404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import time


class IndexListView(ListView):
    template_name = "blog/index.html"
    queryset = Entry.objects.order_by("-created_time").prefetch_related("tags")
    context_object_name = "entries"

    def get_context_data(self, **kwargs):
        context = super(IndexListView, self).get_context_data(**kwargs)

        blogmarks = Blogmark.objects.order_by("-created_time").prefetch_related("tags")
        quotations = Quotation.objects.order_by("-created_time").prefetch_related(
            "tags"
        )
        context["blogmarks"] = blogmarks
        context["quotations"] = quotations
        return context


class EntryDetailView(DateDetailView):
    template_name = "blog/entry_detail.html"
    model = Entry
    context_object_name = "entry"
    date_field = "pub_time"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super(EntryDetailView, self).get_context_data(**kwargs)
        return context


class EntryYearArchiveView(YearArchiveView):
    template_name = "blog/year_archive.html"
    model = Entry
    date_field = "created_time"
    make_object_list = True
    context_object_name = "entry_list"
    allow_empty = True

    def get_context_data(self, **kwargs):
        year = self.kwargs["year"]
        months = []
        for month in range(1, 12 + 1):
            date = datetime.date(year=year, month=month, day=1)
            entry_count = Entry.objects.filter(
                created_time__year=year, created_time__month=month
            ).count()
            quote_count = Quotation.objects.filter(
                created_time__year=year, created_time__month=month
            ).count()
            month_count = entry_count + quote_count
            if month_count:
                counts = [
                    ("entry", entry_count),
                    ("quote", quote_count),
                ]
                counts_not_0 = [p for p in counts if p[1]]
                months.append(
                    {
                        "date": date,
                        "counts": entry_count,
                        "counts_not_0": counts_not_0,
                        "entries": list(
                            Entry.objects.filter(
                                created_time__year=year, created_time__month=month
                            ).order_by("created_time")
                        ),
                    }
                )

        context = super(EntryYearArchiveView, self).get_context_data(**kwargs)
        context["months"] = months
        return context


class EntryMonthArchiveView(MonthArchiveView):
    template_name = "blog/month_archive.html"
    date_field = "created_time"
    model = Entry
    allow_empty = True

    def get_context_data(self, **kwargs):
        year = self.kwargs["year"]
        month = self.kwargs["month"]
        entries = list(
            Entry.objects.filter(
                created_time__year=year, created_time__month=month
            ).order_by("created_time")
        )
        context = super(EntryMonthArchiveView, self).get_context_data(**kwargs)
        context["entries"] = entries
        return context


class EntryDayArchiveView(DayArchiveView):
    template_name = "blog/day_archive.html"
    queryset = Entry.objects.all()
    date_field = "created_time"
    context_object_name = "entry_list"
    allow_empty = True


# This query gets the IDs of things that match all of the tags
INTERSECTION_SQL = """
    SELECT %(content_table)s.id
        FROM %(content_table)s, %(tag_table)s
    WHERE %(tag_table)s.tag_id IN (
            SELECT id FROM blog_tag WHERE tag IN (%(joined_tags)s)
        )
        AND %(tag_table)s.%(tag_table_content_key)s = %(content_table)s.id
    GROUP BY %(content_table)s.id
        HAVING COUNT(%(content_table)s.id) = %(tag_count)d
"""


class TagArchiveView(TemplateView):
    template_name = "blog/tag_archive.html"

    def get_context_data(self, **kwargs):
        tags = self.kwargs["tags"]
        tags = Tag.objects.filter(tag__in=tags.split("+")).values_list(
            "tag", flat=True
        )[:3]
        if not tags:
            raise Http404
        items = []
        from django.db import connection

        cursor = connection.cursor()
        for model, content_type in (
            (Entry, "entry"),
            (Quotation, "quotation"),
            (Blogmark, "blogmark"),
        ):
            cursor.execute(
                INTERSECTION_SQL
                % {
                    "content_table": "blog_%s" % content_type,
                    "tag_table": "blog_%s_tags" % content_type,
                    "tag_table_content_key": "%s_id" % content_type,
                    "joined_tags": ", ".join(["'%s'" % tag for tag in tags]),
                    "tag_count": len(tags),
                }
            )
            ids = [r[0] for r in cursor.fetchall()]
            items.extend(
                [
                    {"type": content_type, "obj": obj}
                    for obj in list(
                        model.objects.prefetch_related("tags").in_bulk(ids).values()
                    )
                ]
            )
        if not items:
            raise Http404
        items.sort(key=lambda x: x["obj"].created_time, reverse=True)

        # Paginate it
        paginator = Paginator(items, 30)
        page_number = self.request.GET.get("page") or "1"
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            raise Http404
        except EmptyPage:
            raise Http404

        context = super(TagArchiveView, self).get_context_data(**kwargs)
        context["tags"] = tags
        context["items"] = page.object_list
        context["total"] = paginator.count
        context["page"] = page
        context["only_one_tag"] = len(tags) == 1
        context["tag"] = Tag.objects.get(tag=tags[0])

        return context


class EntrySearchView(ListView):
    template_name = "blog/search.html"
    model = Entry

    def get_context_data(self, **kwargs):

        q = self.request.GET.get("q", "").strip()
        start = time.time()

        query = None
        rank_annotation = None
        if q:
            query = SearchQuery(q, search_type="websearch")
            rank_annotation = SearchRank(models.F("search_document"), query)

        selected_tags = self.request.GET.getlist("tag")
        excluded_tags = self.request.GET.getlist("exclude.tag")
        selected_type = self.request.GET.get("type", "")
        selected_year = self.request.GET.get("year", "")
        selected_month = self.request.GET.get("month", "")

        values = ["pk", "type", "created_time"]
        if q:
            values.append("rank")

        def make_queryset(klass, type_name):
            qs = klass.objects.annotate(
                type=models.Value(type_name, output_field=models.CharField())
            )
            if selected_year and selected_year.isdigit() and 2000 <= int(selected_year):
                qs = qs.filter(created_time__year=int(selected_year))
            if (
                selected_month
                and selected_month.isdigit()
                and 1 <= int(selected_month) <= 12
            ):
                qs = qs.filter(created_time__month=int(selected_month))
            if q:
                qs = qs.filter(search_document=query)
                qs = qs.annotate(rank=rank_annotation)
            for tag in selected_tags:
                qs = qs.filter(tags__tag=tag)
            for exclude_tag in excluded_tags:
                qs = qs.exclude(tags__tag=exclude_tag)
            return qs.order_by()

        # Start with a .none() queryset just so we can union stuff onto it
        qs = Entry.objects.annotate(
            type=models.Value("empty", output_field=models.CharField())
        )
        if q:
            qs = qs.annotate(rank=rank_annotation)
        qs = qs.values(*values).none()

        type_counts_raw = {}
        tag_counts_raw = {}
        year_counts_raw = {}
        month_counts_raw = {}

        for klass, type_name in (
            (Entry, "entry"),
            (Blogmark, "blogmark"),
            (Quotation, "quotation"),
        ):
            if selected_type and selected_type != type_name:
                continue
            klass_qs = make_queryset(klass, type_name)
            type_count = klass_qs.count()
            if type_count:
                type_counts_raw[type_name] = type_count
            for tag, count in (
                Tag.objects.filter(**{"%s__in" % type_name: klass_qs})
                .annotate(n=models.Count("tag"))
                .values_list("tag", "n")
            ):
                tag_counts_raw[tag] = tag_counts_raw.get(tag, 0) + count
            for row in (
                klass_qs.order_by()
                .annotate(year=TruncYear("created_time"))
                .values("year")
                .annotate(n=models.Count("pk"))
            ):
                year_counts_raw[row["year"]] = (
                    year_counts_raw.get(row["year"], 0) + row["n"]
                )
            # Only do month counts if a year is selected
            if selected_year:
                for row in (
                    klass_qs.order_by()
                    .annotate(month=TruncMonth("created_time"))
                    .values("month")
                    .annotate(n=models.Count("pk"))
                ):
                    month_counts_raw[row["month"]] = (
                        month_counts_raw.get(row["month"], 0) + row["n"]
                    )
            qs = qs.union(klass_qs.values(*values))

        if q:
            qs = qs.order_by("-rank")
        else:
            qs = qs.order_by("-created_time")

        type_counts = sorted(
            [
                {"type": type_name, "n": value}
                for type_name, value in list(type_counts_raw.items())
            ],
            key=lambda t: t["n"],
            reverse=True,
        )
        tag_counts = sorted(
            [{"tag": tag, "n": value} for tag, value in list(tag_counts_raw.items())],
            key=lambda t: t["n"],
            reverse=True,
        )[:40]

        year_counts = sorted(
            [
                {"year": year, "n": value}
                for year, value in list(year_counts_raw.items())
            ],
            key=lambda t: t["year"],
        )

        month_counts = sorted(
            [
                {"month": month, "n": value}
                for month, value in list(month_counts_raw.items())
            ],
            key=lambda t: t["month"],
        )

        paginator = Paginator(qs, 30)
        page_number = self.request.GET.get("page") or "1"
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            raise Http404
        except EmptyPage:
            raise Http404

        results = []
        for obj in load_mixed_objects(page.object_list):
            results.append(
                {
                    "type": obj.original_dict["type"],
                    "rank": obj.original_dict.get("rank"),
                    "obj": obj,
                }
            )
        end = time.time()

        selected = {
            "tags": selected_tags,
            "year": selected_year,
            "month": selected_month,
            "type": selected_type,
        }
        # Remove empty keys
        selected = {key: value for key, value in list(selected.items()) if value}

        # Dynamic title
        noun = {
            "quotation": "Quotations",
            "blogmark": "Blogmarks",
            "entry": "Entries",
        }.get(selected.get("type")) or "Items"
        title = noun

        if q:
            title = "“%s” in %s" % (q, title.lower())

        if selected.get("tags"):
            title += " tagged %s" % (", ".join(selected["tags"]))

        datebits = []
        if selected.get("month_name"):
            datebits.append(selected["month_name"])
        if selected.get("year"):
            datebits.append(selected["year"])
        if datebits:
            title += " in %s" % (", ".join(datebits))

        if not q and not selected:
            title = "Search"

        context = super(EntrySearchView, self).get_context_data(**kwargs)
        context["q"] = q
        context["title"] = title
        context["results"] = results
        context["total"] = paginator.count
        context["page"] = page
        context["duration"] = end - start
        context["type_counts"] = type_counts
        context["tag_counts"] = tag_counts
        context["year_counts"] = year_counts
        context["month_counts"] = month_counts
        context["selected_tags"] = selected_tags
        context["excluded_tags"] = excluded_tags
        context["selected"] = selected
        context["month"] = selected_month

        return context
