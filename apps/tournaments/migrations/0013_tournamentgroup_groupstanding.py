# Generated manually for TournamentGroup and GroupStanding models

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tournaments", "0012_add_round_robin_knockout_format"),
    ]

    operations = [
        migrations.CreateModel(
            name="TournamentGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text='Name of the group (e.g., "Grupo A", "Grupo B")',
                        max_length=100,
                        verbose_name="Group Name",
                    ),
                ),
                (
                    "group_number",
                    models.PositiveIntegerField(
                        help_text="Number of the group within the division",
                        verbose_name="Group Number",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Created At"
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                (
                    "division",
                    models.ForeignKey(
                        help_text="Division this group belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="groups",
                        to="tournaments.tournamentdivision",
                        verbose_name="Division",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tournament Group",
                "verbose_name_plural": "Tournament Groups",
                "ordering": ["division", "group_number"],
                "unique_together": {("division", "group_number")},
                "indexes": [
                    models.Index(fields=["division"], name="tournaments_divisio_abc123_idx"),
                    models.Index(fields=["group_number"], name="tournaments_group_n_xyz789_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="GroupStanding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "matches_played",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Number of matches played",
                        verbose_name="Matches Played",
                    ),
                ),
                (
                    "matches_won",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Number of matches won",
                        verbose_name="Matches Won",
                    ),
                ),
                (
                    "matches_lost",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Number of matches lost",
                        verbose_name="Matches Lost",
                    ),
                ),
                (
                    "sets_won",
                    models.PositiveIntegerField(
                        default=0, help_text="Total sets won", verbose_name="Sets Won"
                    ),
                ),
                (
                    "sets_lost",
                    models.PositiveIntegerField(
                        default=0, help_text="Total sets lost", verbose_name="Sets Lost"
                    ),
                ),
                (
                    "points",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Points accumulated (e.g., 3 for win, 1 for loss)",
                        verbose_name="Points",
                    ),
                ),
                (
                    "position_in_group",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Position within the group",
                        null=True,
                        verbose_name="Position in Group",
                    ),
                ),
                (
                    "global_position",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Global position across all groups",
                        null=True,
                        verbose_name="Global Position",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Created At"
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                (
                    "group",
                    models.ForeignKey(
                        help_text="Group this standing belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="standings",
                        to="tournaments.tournamentgroup",
                        verbose_name="Group",
                    ),
                ),
                (
                    "involvement",
                    models.ForeignKey(
                        help_text="Player or team involvement in the tournament",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="group_standings",
                        to="tournaments.involvement",
                        verbose_name="Involvement",
                    ),
                ),
            ],
            options={
                "verbose_name": "Group Standing",
                "verbose_name_plural": "Group Standings",
                "ordering": ["group", "position_in_group", "global_position"],
                "unique_together": {("group", "involvement")},
                "indexes": [
                    models.Index(fields=["group"], name="tournaments_group__def456_idx"),
                    models.Index(fields=["involvement"], name="tournaments_involv_ghi789_idx"),
                    models.Index(
                        fields=["position_in_group"], name="tournaments_positio_jkl012_idx"
                    ),
                    models.Index(
                        fields=["global_position"], name="tournaments_global__mno345_idx"
                    ),
                    models.Index(fields=["points"], name="tournaments_points_pqr678_idx"),
                ],
            },
        ),
    ]
