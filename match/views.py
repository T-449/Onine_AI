import os
import threading
from multiprocessing import Queue, Process

from django.contrib import messages
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404

from judge_queue.judge_queue import GlobalJudgeQueue
from match import models
from matchExecutionUnit.matchExecutionUnit import execute_match
from myutils import fileutils
# Create your views here.
from django.urls import reverse

import game_creator
from match.models import Match
from myutils.httputils import redirectToCurrent
from submission.models import Submission


def post_create_match(request, workspace_uuid):
    game = game_creator.views.get_game_or_validate_requests(request, workspace_uuid)

    try:
        submission0 = Submission.objects.get(submission_uuid=request.POST['submission0'].strip())
        submission1 = Submission.objects.get(submission_uuid=request.POST['submission1'].strip())
    except:
        raise Http404

    user = request.user
    if not submission0.validate_access(user) or not submission1.validate_access(user):
        raise Http404

    Match.objects.create_test_match(submission0, submission1, game)
    r = HttpResponseRedirect(reverse('game_creator_show_workspace', args=(workspace_uuid,)))
    messages.success(request, 'Saved')

    return r


def get_match_or_validate_requests(request, match_uuid):
    match = get_object_or_404(Match, match_uuid=match_uuid)

    if not match.validate_request(request):
        raise Http404
    return match


def get_match_or_validate_judge_requests(request, match_uuid):
    match = get_object_or_404(Match, match_uuid=match_uuid)

    if not match.validate_judge_request(request):
        raise Http404
    return match


def show_match_history(request, match_uuid):
    match = get_match_or_validate_requests(request, match_uuid)
    if match.match_status != Match.MatchStatus.ENDED:
        return HttpResponseRedirect(reverse("dump_history", args=(match_uuid,)))
    match_history_raw = fileutils.get_file_content_as_string(match.history_filepath)
    match_history = match_history_raw.encode('unicode_escape').decode('utf-8')
    match_result = match.match_results
    match_status = match.match_status
    visualizer = fileutils.get_file_content_as_string(match.game.get_visualization_code_filepath())
    iframe_src_doc = "<html><head><meta charset=\"UTF-8\"><script type=\"text/javascript\"> " + visualizer + \
                     "</script></head> <body>  <script> document.body.onload=function() {" \
                     "test(\'" + match_history + "\');}</script><div id=\"visualizer\"></div></body></html>"
    print(iframe_src_doc)

    context = {
        "match": match,
        "result": match_result,
        "match_history_raw": match_history_raw,
        "match_history": match_history,
        "iframe_src_doc": iframe_src_doc
    }
    return render(request, 'match/match_history.html', context)


def judge_match(request, match_uuid):
    match = get_match_or_validate_judge_requests(request, match_uuid)
    print("Hello ", match, os.getpid(), os.getpgrp())
    GlobalJudgeQueue.judge_queue.submit(match)

    # p = Process(target=execute_match, args=(match,))
    # p.start()

    return redirectToCurrent(request)


def delete_match(request, match_uuid):
    match = get_match_or_validate_judge_requests(request, match_uuid)
    if match.match_visibility != Match.MatchVisibility.WORKSPACE_TEST_MATCH:
        print("User ", request.user, " is trying to delete match ", match)
        messages.error(request, "You can not delete this match")
        return redirectToCurrent(request)
    try:
        os.remove(match.history_filepath)
    except IsADirectoryError:
        pass
    except FileNotFoundError:
        pass
    models.Match.objects.filter(match_uuid=match_uuid).delete()
    return redirectToCurrent(request)


def dump_match_history(request, match_uuid):
    try:
        match = get_match_or_validate_requests(request, match_uuid)
        match_history_raw = fileutils.get_file_content_as_string(match.history_filepath)

        response = HttpResponse(match_history_raw, content_type="text/plain")
        response['Content-Disposition'] = 'inline; '
        return response
    except:
        raise Http404
