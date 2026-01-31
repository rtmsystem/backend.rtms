# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0014_rename_tournaments_group__def456_idx_tournaments_group_i_beded4_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='involvement',
            name='knockout_points',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Points accumulated from knockout/bracket match wins',
                verbose_name='Knockout Points'
            ),
        ),
        migrations.AddIndex(
            model_name='involvement',
            index=models.Index(fields=['-knockout_points'], name='tournaments_knockou_abc123_idx'),
        ),
    ]
