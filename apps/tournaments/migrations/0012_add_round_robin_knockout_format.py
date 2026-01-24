# Generated manually for Round Robin + Knockout format

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tournaments", "0011_alter_tournament_banner_alter_tournament_logo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tournamentdivision",
            name="format",
            field=models.CharField(
                choices=[
                    ("knockout", "Single Elimination"),
                    ("double_slash", "Double Elimination"),
                    ("round_robin", "Round Robin"),
                    ("round_robin_knockout", "Round Robin + Knockout"),
                ],
                help_text="Tournament format for this division",
                max_length=20,
                verbose_name="Format",
            ),
        ),
    ]
