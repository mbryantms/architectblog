# Generated by Django 3.2.5 on 2021-07-29 12:34

from django.conf import settings
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="entry",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="author",
            ),
        ),
        migrations.AddField(
            model_name="entry",
            name="series",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="entries",
                to="blog.series",
            ),
        ),
        migrations.AddField(
            model_name="entry",
            name="tags",
            field=models.ManyToManyField(blank=True, to="blog.Tag"),
        ),
        migrations.AddField(
            model_name="blogmark",
            name="tags",
            field=models.ManyToManyField(blank=True, to="blog.Tag"),
        ),
        migrations.AddIndex(
            model_name="quotation",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_document"], name="blog_quotat_search__aa2d47_gin"
            ),
        ),
        migrations.AddIndex(
            model_name="blogmark",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_document"], name="blog_blogma_search__45eeb9_gin"
            ),
        ),
    ]
