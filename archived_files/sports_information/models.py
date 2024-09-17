import datetime
from datetime import timedelta, date
from django.db import models
from .utility import model_helpers as mh
import general_information.models as gn_models
from django.core.validators import MinValueValidator  # MaxValueValidator,


class Season(models.Model):
    year_range_id = models.ForeignKey(
        gn_models.YearRange, on_delete=models.CASCADE,
        related_name="season_start_year", verbose_name="Year Range")
    start_day = models.DateField(default=date.today)
    num_of_weeks = models.IntegerField(default=1, help_text="Number of weeks \
                                       in the season",
                                       verbose_name="Number of Weeks",
                                       validators=[MinValueValidator(1)])
    sport_id = models.ForeignKey(
        gn_models.Sport, on_delete=models.CASCADE,
        related_name="sport_type_id", verbose_name="Sport")
    """ created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    updated_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
     editable=False, related_name="year_updated_by")
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
     editable=False, related_name="year_created_by")"""

    def __str__(self):
        try:
            return str(self.year_range_id.start_year) + " " + \
                str(self.sport_id)
        except LookupError:
            return "No Season"

    class Meta:
        ordering = ["year_range_id", "sport_id"]
        unique_together = ('year_range_id', 'sport_id')


class Week(models.Model):
    season_id = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="week_season",
        verbose_name="Season")
    start_day = models.DateField(
        default=datetime.datetime.today, verbose_name="Start Day")
    end_day = models.DateField(editable=False, default=date.today(
    ) + timedelta(days=6), verbose_name="End Day")
    num = models.IntegerField(default=1, verbose_name="Set Number")
    sub_week = models.IntegerField(default=1, verbose_name="Sub Set")
    """ created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    updated_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
      editable=False, related_name="week_updated_by")
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
      editable=False, related_name="week_created_by")"""

    def __str__(self):
        try:
            return "Game Set " + str(self.num) + "." + str(self.sub_week) + \
                ", " + str(self.season_id)
        except LookupError:
            return "No Game Set"

    class Meta:
        verbose_name = "Game Set"
        ordering = ["season_id", "num", "sub_week"]
        unique_together = ('season_id', 'num', 'sub_week')


class Team(models.Model):
    state_id = models.ForeignKey(
        gn_models.State, on_delete=models.CASCADE, verbose_name="State")
    city_id = models.ForeignKey(
        gn_models.City, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="City")
    name = models.CharField(max_length=50, verbose_name="Name")
    team_num = models.IntegerField(default=1, verbose_name="ID")
    football_stadium_id = models.ForeignKey(
        gn_models.Stadium, on_delete=models.SET_NULL,
        related_name="football_stadium", null=True, blank=True,
        verbose_name="Football Stadium")
    basketball_stadium_id = models.ForeignKey(
        gn_models.Stadium, on_delete=models.SET_NULL,
        related_name="basketball_stadium", null=True,
        blank=True, verbose_name="Basketball Stadium")
    soccer_stadium_id = models.ForeignKey(
        gn_models.Stadium, on_delete=models.SET_NULL,
        related_name="soccer_stadium", null=True,
        blank=True, verbose_name="Soccer Stadium")
    division_id = models.ForeignKey(
        gn_models.Division, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Division")
    conference_id = models.ForeignKey(
        gn_models.Conference, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Conference")
    level = models.CharField(max_length=20, choices=mh.SPORT_LEVEL)
    # created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True, editable=False)
    # updated_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
    # editable=False, related_name="school_updated_by")
    # created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
    # editable=False, related_name="school_created_by")

    def __str__(self):
        try:
            return self.name
        except LookupError:
            return "No Team"

    class Meta:
        verbose_name_plural = "Teams"
        ordering = ["name", "state_id"]
        unique_together = ["name", "state_id", "level"]


# Links teams to what seasons they are in for access in team page
class TeamSeasonLinker(models.Model):
    team_id = models.ForeignKey(
        Team, on_delete=models.CASCADE, verbose_name="Team")
    season_id = models.ForeignKey(
        Season, on_delete=models.CASCADE, verbose_name="Season")
    # updated_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
    # editable=False, related_name="team_season_linker_updated_by")
    # created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
    # editable=False, related_name="team_season_linker_created_by")

    def __str__(self):
        try:
            return str(self.team_id) + " " + str(self.season_id)
        except LookupError:
            return "No TeamSeasonLinker"

    class Meta:
        verbose_name = "Team Season Linker"
        ordering = ["team_id", "season_id"]
        unique_together = ["team_id", "season_id"]


class TeamWeeklyData(models.Model):
    team_id = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Team")
    week_id = models.ForeignKey(
        Week, on_delete=models.CASCADE, verbose_name="Week")
    actual_change = models.FloatField(default=0)
    total_score = models.FloatField(default=0)
    num_games = models.FloatField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    ties = models.IntegerField(default=0)
    power = models.FloatField(default=0)
    overall_rank = models.IntegerField(default=0, verbose_name="Rank")
    recent_opponent_1 = models.IntegerField(default=0)
    recent_opponent_2 = models.IntegerField(default=0)
    recent_opponent_3 = models.IntegerField(default=0)
    recent_opponent_4 = models.IntegerField(default=0)
    recent_opponent_5 = models.IntegerField(default=0)
    div_rank = models.IntegerField(default=0)
    last_rank = models.IntegerField(default=0)
    """ as_of = models.DateField(default=timezone.now, editable=False)
    created = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
    editable=False,related_name="football_team_created_by")
    updated = models.DateTimeField(auto_now_add=True, editable=False)
    updated_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
    editable=False,related_name="football_team_updated_by") """

    def __str__(self):
        try:
            return self.team_id.name + " " + str(self.week_id)
        except LookupError:
            return "No Team Weekly Data"

    class Meta:
        ordering = ["-power"]
        verbose_name_plural = "Weekly Data"


class Game(models.Model):
    home_team_id = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="football_home_team",
        null=True, blank=True, verbose_name="Home Team")
    visitor_team_id = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="football_visitor_team",
        null=True, blank=True, verbose_name="Visitor Team")
    original_home_score = models.IntegerField(default=0, verbose_name="Home")
    original_visitor_score = models.IntegerField(
        default=0, verbose_name="Visitor")
    home_z_score = models.FloatField(default=0)
    visitor_z_score = models.FloatField(default=0)
    week_id = models.ForeignKey(Week, on_delete=models.SET_NULL,
                                related_name="football_game_week", null=True,
                                blank=True, verbose_name="Week")
    flagged = models.BooleanField(
        default=False, help_text="Has the game score been flagged?")
    invalid = models.BooleanField(
        default=False, help_text="Does this game break the algorithm?")
    home_field_advantage = models.BooleanField(
        default=True, verbose_name="Home Field")
    # as_of = models.DateField(default=timezone.now, editable=False)
    # created = models.DateTimeField(auto_now=True, editable=False)
    # created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
    # editable=False,related_name="football_game_created_by")
    # updated = models.DateTimeField(auto_now_add=True, editable=False)
    # updated_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,
    # editable=False,related_name="football_game_updated_by")

    class Meta:
        ordering = ["week_id", "home_team_id"]
        unique_together = ["week_id", "home_team_id", "visitor_team_id",
                           "home_field_advantage", "original_home_score",
                           "original_visitor_score"]
