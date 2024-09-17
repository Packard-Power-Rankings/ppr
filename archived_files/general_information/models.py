from datetime import datetime
from django.db import models
from .utility import model_helpers as mh


class State(models.Model):
    name = models.CharField(unique=True, max_length=20)
    code = models.CharField(
        max_length=5,
        unique=True,
        help_text="Acronym: e.g. CO for Colorado")
    # created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True, editable=False)
    # updated_by = models.ForeignKey(
    #     User, on_delete=models.SET_NULL, null=True, editable=False,
    #     related_name="state_updated_by")
    # created_by = models.ForeignKey(
    #     User, on_delete=models.SET_NULL, null=True, editable=False,
    #     related_name="state_created_by")

    def __str__(self):
        try:
            return self.name
        except BaseException:
            return "No State"

    class Meta:
        ordering = ["name"]
        unique_together = ('name', 'code')


class YearRange(models.Model):
    start_year = models.IntegerField(
        default=datetime.now().year,
        help_text="Year the season started")
    end_year = models.IntegerField(
        default=datetime.now().year + 1,
        help_text="Year the season ended")
    # created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True, editable=False)
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
    #                                null=True, editable=False,
    #                                related_name="start_year_updated_by")
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
    #                                null=True, editable=False,
    #                                related_name="start_year_created_by")

    def __str__(self):
        try:
            return str(self.start_year) + "-" + str(self.end_year)
        except BaseException:
            return "No Year"

    class Meta:
        ordering = ["start_year", "end_year"]
        verbose_name_plural = "Year Ranges"
        unique_together = ('start_year', 'end_year')


class City(models.Model):
    name = models.CharField(max_length=25)
    state_id = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        verbose_name="State")
    # created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True, editable=False)
    # updated_by = models.ForeignKey(
    #     User, on_delete=models.SET_NULL, null=True, editable=False,
    #     related_name="city_updated_by")
    # created_by = models.ForeignKey(
    #     User, on_delete=models.SET_NULL, null=True, editable=False,
    #     related_name="city_created_by")

    def __str__(self):
        try:
            return self.name
        except BaseException:
            return "No City"

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Cities"
        unique_together = ('name', 'state_id')


class Conference(models.Model):
    name = models.CharField(
        unique=True,
        max_length=25,
        help_text="Name of the conference")
    # created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True, editable=False)
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
    #                                null=True, editable=False,
    #                                related_name="stadium_updated_by",)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
    #                                null=True, editable=False,
    #                                related_name="stadium_created_by",)

    def __str__(self):
        try:
            return self.name
        except BaseException:
            return "No Conference"

    class Meta:
        ordering = ["name"]


class Stadium(models.Model):
    name = models.CharField(
        unique=True,
        max_length=25,
        help_text="Name of the stadium")
    # created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True, editable=False)
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
    #                                null=True, editable=False,
    #                                related_name="stadium_updated_by",)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
    #                                null=True, editable=False,
    #                                related_name="stadium_created_by",)

    def __str__(self):
        try:
            return self.name
        except BaseException:
            return "No Stadium"

    class Meta:
        ordering = ["name"]


class Division(models.Model):
    name = models.CharField(
        unique=True,
        max_length=25,
        help_text="Division Name, e.g., 5A")
    # created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True, editable=False)
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
    #                                null=True, editable=False,
    #                                related_name="division_updated_by")
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
    #                                null=True, editable=False,
    #                                related_name="division_created_by")

    def __str__(self):
        try:
            return self.name
        except BaseException:
            return "No Division"

    class Meta:
        ordering = ["name"]


class Sport(models.Model):
    name = models.CharField(max_length=18, choices=mh.SPORT_CHOICES)
    level = models.CharField(max_length=20, choices=mh.SPORT_LEVEL)
    k_value = models.FloatField(default=0.7, null=False)
    home_advantage = models.FloatField(default=3.0, null=False)
    average_game_score = models.FloatField(default=50, null=False)
    game_set_len = models.IntegerField(default=7, null=False)
    # created = models.DateTimeField(auto_now_add=True, editable=False)
    # updated = models.DateTimeField(auto_now=True, editable=False)
    # updated_by = models.ForeignKey(
    #     User, on_delete=models.SET_NULL, null=True, editable=False,
    #     related_name="sport_updated_by")
    # created_by = models.ForeignKey(
    #     User, on_delete=models.SET_NULL, null=True, editable=False,
    #     related_name="sport_created_by")

    def __str__(self):
        try:
            return f"{self.level} {self.name}"
        except BaseException:
            return "No Sport"

    class Meta:
        ordering = ["name", "level"]
        unique_together = ('name', 'level')