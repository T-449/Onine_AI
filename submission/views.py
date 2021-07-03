import os

from django.contrib.auth.decorators import login_required
from django.utils import timezone


from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse

import game_creator
from . import models
from django.shortcuts import get_object_or_404


# Create your views here.
def get_submission_or_validate_requests(request, submission_uuid):
    submission = get_object_or_404(models.Submission, submission_uuid=submission_uuid)
    if not request.user.is_authenticated or \
            not submission.validate_access(request.user):
        raise Http404
    return submission


def show_raw_submission(request, submission_uuid):
    submission = get_submission_or_validate_requests(request, submission_uuid)
    file_path = submission.get_submission_filepath()

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="text/plain")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def delete_submission(request, submission_uuid):
    submission = get_submission_or_validate_requests(request, submission_uuid)
    file_path = submission.get_submission_filepath()

    models.Submission.objects.filter(submission_uuid=submission_uuid).delete()
    os.remove(file_path)
    return  HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def post_test_submission(request, workspace_uuid):

    lang = request.POST['submission_language']
    code = request.POST['submission_code']
    tag = request.POST['tag']
    time = now = timezone.now()

    game = game_creator.views.get_game_or_validate_requests(request, workspace_uuid)

    user = request.user
    submission = models.Submission.objects.create_test_submission(user, time, code, lang, game, tag)
    submission.save()
    r = HttpResponseRedirect(reverse('game_creator_show_workspace', args=(workspace_uuid,)))
    messages.success(request, 'Saved')
    return r
