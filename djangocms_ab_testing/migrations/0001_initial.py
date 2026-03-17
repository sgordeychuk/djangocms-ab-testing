from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cms', '0022_auto_20180620_1551'),
    ]

    operations = [
        migrations.CreateModel(
            name='ABTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=64, unique=True)),
                ('description', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'AB Test',
                'verbose_name_plural': 'AB Tests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ABCounter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_name', models.CharField(max_length=64, unique=True)),
                ('count', models.PositiveIntegerField(default=0)),
                ('test', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='counter', to='djangocms_ab_testing.abtest')),
            ],
            options={
                'verbose_name': 'AB Counter',
                'verbose_name_plural': 'AB Counters',
            },
        ),
        migrations.CreateModel(
            name='ABEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant', models.CharField(max_length=2)),
                ('action', models.CharField(max_length=20)),
                ('session_key', models.CharField(db_index=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meta', models.JSONField(blank=True, default=dict)),
                ('test', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='djangocms_ab_testing.abtest')),
            ],
            options={
                'verbose_name': 'AB Event',
                'verbose_name_plural': 'AB Events',
                'indexes': [
                    models.Index(fields=['test', 'action', 'created_at'], name='djangocms_a_test_id_d7e8f0_idx'),
                    models.Index(fields=['test', 'variant'], name='djangocms_a_test_id_a1b2c3_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ABTestPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='%(app_label)s_%(class)s', serialize=False, to='cms.cmsplugin')),
                ('is_active', models.BooleanField(default=True)),
                ('forced_variant', models.CharField(blank=True, default='', help_text="Leave empty for normal rotation. Set a variant key (e.g. 'A' or 'B') to always show that variant.", max_length=2, verbose_name='Force variant (debug)')),
                ('test', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='djangocms_ab_testing.abtest', verbose_name='AB Test')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='ABTestVariantPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='%(app_label)s_%(class)s', serialize=False, to='cms.cmsplugin')),
                ('variant_name', models.CharField(max_length=100)),
                ('variant_key', models.CharField(max_length=2)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
