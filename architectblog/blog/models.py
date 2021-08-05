from django.db import models
from django.utils.timezone import now
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.conf import settings
from django.utils.text import Truncator
from django.utils.html import strip_tags, escape
from tinymce.models import HTMLField
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from collections import Counter
import re

tag_re = re.compile("^[a-z0-9]+$")


class Tag(models.Model):
    tag = models.SlugField(unique=True)

    def __str__(self):
        return self.tag

    def get_absolute_url(self):
        return reverse("blog:tag_detail", args=[self.tag])

    def get_link(self, reltag=False):
        return mark_safe(
            '<a href="%s"%s>%s</a>'
            % (self.get_absolute_url(), (reltag and ' rel="tag"' or ""), self)
        )

    def get_reltag(self):
        return self.get_link(reltag=True)

    def entry_count(self):
        return self.entry_set.count()

    def link_count(self):
        return self.blogmark_set.count()

    def quote_count(self):
        return self.quotation_set.count()

    def total_count(self):
        return self.entry_count() + self.link_count() + self.quote_count()

    def all_types_queryset(self):
        entries = (
            self.entry_set.all()
            .annotate(type=models.Value("entry", output_field=models.CharField()))
            .values("pk", "created", "type")
        )
        blogmarks = (
            self.blogmark_set.all()
            .annotate(type=models.Value("blogmark", output_field=models.CharField()))
            .values("pk", "created", "type")
        )
        quotations = (
            self.quotation_set.all()
            .annotate(type=models.Value("quotation", output_field=models.CharField()))
            .values("pk", "created", "type")
        )
        return entries.union(blogmarks, quotations).order_by("-created")

    def get_related_tags(self, limit=10):
        """Get all items tagged with this, look at /their/ tags, order by count"""
        if not hasattr(self, "_related_tags"):
            counts = Counter()
            for klass, collection in (
                (Entry, "entry_set"),
                (Blogmark, "blogmark_set"),
                (Quotation, "quotation_set"),
            ):
                qs = klass.objects.filter(
                    pk__in=getattr(self, collection).all()
                ).values_list("tags__tag", flat=True)
                counts.update(t for t in qs if t != self.tag)
            tag_names = [p[0] for p in counts.most_common(limit)]
            tags_by_name = {t.tag: t for t in Tag.objects.filter(tag__in=tag_names)}
            # Need a list in the correct order
            self._related_tags = [tags_by_name[name] for name in tag_names]
        return self._related_tags


class BaseModel(models.Model):
    created_time = models.DateTimeField(
        verbose_name="Creation time", default=timezone.now
    )
    tags = models.ManyToManyField(Tag, blank=True)
    slug = models.SlugField(max_length=64)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    metadata = models.JSONField(blank=True, default=dict)
    search_document = SearchVectorField(null=True)

    @property
    def type(self):
        return self._meta.model_name

    def tag_summary(self):
        return " ".join(t.tag for t in self.tags.all())

    class Meta:
        abstract = True
        ordering = ("-created_time",)
        indexes = [GinIndex(fields=["search_document"])]


class Series(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("series-detail", args=[self.slug])

    def get_entries_in_order(self):
        return self.entries.order_by("created_time")


class Entry(BaseModel):
    STATUS_CHOICES = (
        ("d", "draft"),
        ("p", "published"),
    )

    title = models.CharField("title", max_length=300, unique=True)
    content = HTMLField()
    pub_time = models.DateTimeField(
        "publication time", blank=False, null=False, default=now
    )
    status = models.CharField(
        "status", max_length=1, choices=STATUS_CHOICES, default="p"
    )
    views = models.PositiveIntegerField("views", default=0)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="author",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )
    series = models.ForeignKey(
        Series, related_name="entries", blank=True, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return (
            self.title
            if self.title
            else Truncator(strip_tags(self.content)).words(15, truncate=" …")
        )

    def get_absolute_url(self):
        return reverse(
            "blog:entry_detail",
            kwargs={
                "slug": self.slug,
                "year": self.pub_time.year,
                "month": self.pub_time.strftime("%m"),
                "day": self.pub_time.day,
            },
        )

    def index_components(self):
        return {
            "A": self.title,
            "C": strip_tags(self.content),
            "B": " ".join(self.tags.values_list("tag", flat=True)),
        }

    class Meta:
        verbose_name_plural = "entries"


class Blogmark(BaseModel):
    link_url = models.URLField(max_length=1000)
    link_title = models.CharField(max_length=255)
    via_url = models.URLField(blank=True, null=True)
    via_title = models.CharField(max_length=255, blank=True, null=True)
    commentary = models.TextField()

    is_blogmark = True

    def index_components(self):
        return {
            "A": self.link_title,
            "B": " ".join(self.tags.values_list("tag", flat=True)),
            "C": self.commentary
            + " "
            + self.link_domain()
            + " "
            + (self.via_title or ""),
        }

    def __str__(self):
        return self.link_title

    def link_domain(self):
        return self.link_url.split("/")[2]

    def word_count(self):
        count = len(self.commentary.split())
        if count == 1:
            return "1 word"
        else:
            return "%d words" % count

    def get_absolute_url(self):
        return reverse(
            "blog:link_detail",
            kwargs={
                "slug": self.slug,
                "year": self.created_time.year,
                "month": self.created_time.strftime("%m"),
                "day": self.created_time.day,
            },
        )


class Quotation(BaseModel):
    quotation = models.TextField()
    source = models.CharField(max_length=255)
    source_url = models.URLField(blank=True, null=True)

    is_quotation = True

    def index_components(self):
        return {
            "A": self.quotation,
            "B": " ".join(self.tags.values_list("tag", flat=True)),
            "C": self.source,
        }

    def __str__(self):
        return self.quotation

    def get_absolute_url(self):
        return reverse(
            "blog:quote_detail",
            kwargs={
                "slug": self.slug,
                "year": self.created_time.year,
                "month": self.created_time.strftime("%m"),
                "day": self.created_time.day,
            },
        )


def load_mixed_objects(dicts):
    """
    Takes a list of dictionaries, each of which must at least have a 'type'
    and a 'pk' key. Returns a list of ORM objects of those various types.
    Each returned ORM object has a .original_dict attribute populated.
    """
    to_fetch = {}
    for d in dicts:
        to_fetch.setdefault(d["type"], set()).add(d["pk"])
    fetched = {}
    for key, model in (
        ("blogmark", Blogmark),
        ("entry", Entry),
        ("quotation", Quotation),
    ):
        ids = to_fetch.get(key) or []
        objects = model.objects.prefetch_related("tags").filter(pk__in=ids)
        for obj in objects:
            fetched[(key, obj.pk)] = obj
    # Build list in same order as dicts argument
    to_return = []
    for d in dicts:
        item = fetched.get((d["type"], d["pk"])) or None
        if item:
            item.original_dict = d
        to_return.append(item)
    return to_return
