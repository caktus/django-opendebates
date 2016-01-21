# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0012_auto_20151227_1431'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.TextField(max_length=3000, verbose_name='comment')),
                ('submit_date', models.DateTimeField(default=None, verbose_name='date/time submitted', db_index=True)),
                ('ip_address', models.GenericIPAddressField(unpack_ipv4=True, null=True, verbose_name='IP address', blank=True)),
                ('is_public', models.BooleanField(default=True, help_text='Uncheck this box to make the comment effectively disappear from the site.', db_index=True, verbose_name='is public')),
                ('is_removed', models.BooleanField(default=False, help_text='Check this box if the comment is inappropriate. A "This comment has been removed" message will be displayed instead.', db_index=True, verbose_name='is removed')),
                ('object', models.ForeignKey(related_name='comments', to='opendebates.Submission')),
                ('user', models.ForeignKey(related_name='comments', verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('submit_date',),
                'db_table': 'opendebates_comments',
                'verbose_name': 'comment',
                'verbose_name_plural': 'comments',
                'permissions': [('can_moderate', 'Can moderate comments')],
            },
        ),
        migrations.CreateModel(
            name='CommentFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flag', models.CharField(max_length=30, verbose_name='flag', db_index=True)),
                ('flag_date', models.DateTimeField(default=None, verbose_name='date')),
                ('comment', models.ForeignKey(related_name='flags', verbose_name='comment', to='opendebates_comments.Comment')),
                ('user', models.ForeignKey(related_name='comment_flags', verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'opendebates_comment_flags',
                'verbose_name': 'comment flag',
                'verbose_name_plural': 'comment flags',
            },
        ),
        migrations.AlterUniqueTogether(
            name='commentflag',
            unique_together=set([('user', 'comment', 'flag')]),
        ),
    ]
