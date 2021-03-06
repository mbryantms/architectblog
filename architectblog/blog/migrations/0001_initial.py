# Generated by Django 3.2.5 on 2021-07-29 12:34

import django.contrib.postgres.search
from django.db import migrations, models
import django.utils.timezone
import tinymce.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Blogmark",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_time",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Creation time"
                    ),
                ),
                ("slug", models.SlugField(max_length=64)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "search_document",
                    django.contrib.postgres.search.SearchVectorField(null=True),
                ),
                ("link_url", models.URLField(max_length=1000)),
                ("link_title", models.CharField(max_length=255)),
                ("via_url", models.URLField(blank=True, null=True)),
                ("via_title", models.CharField(blank=True, max_length=255, null=True)),
                ("commentary", models.TextField()),
            ],
            options={
                "ordering": ("-created_time",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Entry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_time",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Creation time"
                    ),
                ),
                ("slug", models.SlugField(max_length=64)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "search_document",
                    django.contrib.postgres.search.SearchVectorField(null=True),
                ),
                (
                    "title",
                    models.CharField(max_length=300, unique=True, verbose_name="title"),
                ),
                ("content", tinymce.models.HTMLField()),
                (
                    "pub_time",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="publication time",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("d", "draft"), ("p", "published")],
                        default="p",
                        max_length=1,
                        verbose_name="status",
                    ),
                ),
                ("views", models.PositiveIntegerField(default=0, verbose_name="views")),
            ],
            options={
                "verbose_name_plural": "entries",
            },
        ),
        migrations.CreateModel(
            name="Series",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=300)),
                ("slug", models.SlugField()),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "verbose_name_plural": "series",
            },
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("tag", models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Quotation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_time",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Creation time"
                    ),
                ),
                ("slug", models.SlugField(max_length=64)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "search_document",
                    django.contrib.postgres.search.SearchVectorField(null=True),
                ),
                ("quotation", models.TextField()),
                ("source", models.CharField(max_length=255)),
                ("source_url", models.URLField(blank=True, null=True)),
                ("tags", models.ManyToManyField(blank=True, to="blog.Tag")),
            ],
            options={
                "ordering": ("-created_time",),
                "abstract": False,
            },
        ),
    ]
