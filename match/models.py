import os
import traceback
import uuid

import django.contrib.auth.models
from django.db import models
from django.utils import timezone

from Online_AI import settings
from submission.models import Submission
from game_creator.models import Game, GameCreatorWorkspaceACL
from tournament.models import Tournament


# Create your models here.

class MatchManager(models.Manager):
    def create_tournament_match(self, submission0, submission1, tournament):
        match = self.create(submission0=submission0, submission1=submission1, game=tournament.game,
                            match_visibility=Match.MatchVisibility.PUBLIC)
        path = os.path.join(settings.MEDIA_ROOT, 'matches/' + str(match.match_uuid))
        match.history_filepath = path + '/matchhistory.json'
        match.save()

        try:
            TournamentMatchTable.objects.create(tournament=tournament, match=match)
        except:
            TournamentMatchTable.objects.filter(pk=match.pk).delete()
            return None

        os.makedirs(path, exist_ok=True)
        return match

    def create_tournament_test_match(self, submission0, submission1, tournament, user):
        match = self.create(submission0=submission0, submission1=submission1, game=tournament.game,
                            match_visibility=Match.MatchVisibility.PRIVATE)

        path = os.path.join(settings.MEDIA_ROOT, 'matches/' + str(match.match_uuid))
        match.history_filepath = path + '/matchhistory.json'
        match.save()

        try:
            TournamentTestMatchTable.objects.create(tournament=tournament, match=match, user=user)
        except:
            TournamentTestMatchTable.objects.filter(pk=match.pk).delete()
            return None

        os.makedirs(path, exist_ok=True)

        return match

    def create_test_match(self, submission0, submission1, workspace):
        match = self.create(submission0=submission0, submission1=submission1, game=workspace,
                            match_visibility=Match.MatchVisibility.WORKSPACE_TEST_MATCH)
        path = os.path.join(settings.MEDIA_ROOT, 'matches/' + str(match.match_uuid))
        os.makedirs(path, exist_ok=True)
        match.history_filepath = path + '/matchhistory.json'
        match.save()
        try:
            WorkspaceMatchTable.objects.create(workspace=workspace, match=match, time=timezone.now())
        except:
            traceback.print_exc()
            WorkspaceMatchTable.objects.filter(pk=match.pk).delete()
            return None

        return match


class Match(models.Model):
    class MatchStatus(models.IntegerChoices):
        PENDING = 0
        ERROR = -1
        RUNNING = 1
        ENDED = 2

    class MatchVisibility(models.IntegerChoices):
        PUBLIC = 0
        PRIVATE = 1
        WORKSPACE_TEST_MATCH = 2

    match_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    # match_status = models.CharField(max_length=10, null=False, default='Pending')
    match_status = models.IntegerField(default=MatchStatus.PENDING, choices=MatchStatus.choices, null=False)
    match_results = models.CharField(max_length=10, null=False, default='Not Decided')
    match_visibility = models.IntegerField(choices=MatchVisibility.choices, null=False, default=MatchVisibility.PRIVATE)
    submission0 = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='player0_submission')
    submission1 = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='player1_submission')
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    history_filepath = models.FilePathField(null=True)

    objects = MatchManager()

    @property
    def resultDescription(self):
        if self.match_results is not None:
            if self.match_results.lower() == "not decided":
                match_result = "Not Decided"
            elif self.match_results.lower() == "win":
                match_result = "Player 1 won"
            elif self.match_results.lower() == "loss":
                match_result = "Player 2 won"
            elif self.match_results.lower() == "draw":
                match_result = "Game drawn"
            else:
                match_result = "Error"
        return match_result

    def validate_request(self, request):
        workspace = self.game
        user = request.user

        if self.match_visibility == Match.MatchVisibility.PRIVATE:
            u = TournamentTestMatchTable.objects.get(match=self).user
            print(u, user, u == user)
            return u == user
        elif self.match_visibility == Match.MatchVisibility.PUBLIC:
            return True
        elif self.match_visibility == Match.MatchVisibility.WORKSPACE_TEST_MATCH:
            try:
                GameCreatorWorkspaceACL.objects.get(user=user, game=workspace)
                return True
            except:
                return False

    def validate_judge_request(self, request):
        workspace = self.game
        user = request.user
        if self.match_visibility == Match.MatchVisibility.PUBLIC:
            return False
        elif self.match_visibility == Match.MatchVisibility.WORKSPACE_TEST_MATCH:
            try:
                GameCreatorWorkspaceACL.objects.get(user=user, game=workspace)
                return True
            except:
                return False
        elif self.match_visibility == Match.MatchVisibility.PRIVATE:
            try:
                return TournamentTestMatchTable.objects.get(match=self).user == user
            except:
                return False


class TournamentMatchTable(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)


class TournamentTestMatchTable(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    user = models.ForeignKey(django.contrib.auth.models.User, on_delete=models.CASCADE)


class WorkspaceMatchTable(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Game, on_delete=models.CASCADE)
    time = models.DateTimeField(null=True)
