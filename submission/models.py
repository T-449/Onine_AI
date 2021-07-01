import os.path
import uuid

import game_creator.models
from Online_AI import settings
from myutils import fileutils
from django.db import models
from game_creator.models import Game
from game_creator.models import GameCreatorWorkspaceACL

import django.contrib.auth.models


# Create your models here.
class SubmissionManager(models.Manager):
    def create_test_submission(self, user, time, code, language, workspace):
        submission = self.create(user=user)
        submission.submission_time = time
        submission.submission_language = language
        submission.submission_status = "test"

        fileutils.write_string_to_file(submission.get_submission_filepath(), code)

        try:
            WorkspaceTestSubmissionEntry.objects.create(game=workspace, submission=submission)
        except:
            Submission.objects.filter(pk=submission.pk).delete()

        return submission


class Submission(models.Model):
    submission_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    submission_time = models.DateTimeField(null=True)
    user = models.ForeignKey(django.contrib.auth.models.User, on_delete=models.CASCADE)
    submission_language = models.CharField(max_length=10, default='')
    submission_status = models.CharField(max_length=10, default='public')

    objects = SubmissionManager()

    def upload_submission_file_from_string(self, string):
        fileutils.write_string_to_file(self.get_submission_filepath(), string)

    def get_submission_url(self):
        return 'raw/' + str(self.submisson_uuid)

    def get_submission_filepath(self):
        return os.path.join(settings.MEDIA_ROOT, 'submissions', str(self.submission_uuid))

    def validate_access(self, user):
        if self.submission_status == "private":
            return self.user == user
        elif self.submission_status == "test":
            game = WorkspaceTestSubmissionEntry.objects.get(submission=self).game
            return game_creator.models.game_creator_validate_workspace_access(user, game)
        else:
            return True


class WorkspaceTestSubmissionEntry(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

# from submission.models import Submission
# from django.contrib.auth.models import User
# from game_creator.models import Game
# u = User.objects.get(pk=1)
# g = Game.objects.get(pk=1)
# lang='c++'
# import datetime
# dt = datetime.datetime.now()
# code='hello'
# c = Submission.objects.create_test_submission(u,dt,code,lang,g)
