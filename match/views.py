from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

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
        submission0 = Submission.objects.get(submission_uuid=request.POST['submission0'])
        submission1 = Submission.objects.get(submission_uuid=request.POST['submission1'])
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
    match_history = fileutils.get_file_content_as_string(match.history_filepath)
    match_result = "Not Decided"
    visualizer = fileutils.get_file_content_as_string(match.game.get_visualization_code_filepath())
    iframe_src_doc = "<html><head></head><script type=\"text/javascript\"> " + visualizer + \
                     "</script> <body  onload=\"test()\"><div id=\"visualizer\"></div></body></html>"
    print(iframe_src_doc)

    if match.match_results is not None:
        if match.match_results == "win":
            match_result = "Player 1(" + match.submission0.user.username + ") won"
        elif match.match_results == "Player":
            match_result = "Player 2(" + match.submission1.user.username + ") won"
        elif match.match_results == "draw":
            match_result = "The Game drawn"
        else:
            match_result = "Error"

    context = {
        "match": match,
        "result": match_result,
        "match_history": match_history,
        "iframe_src_doc": iframe_src_doc
    }
    return render(request, 'match/match_history.html', context)


def judge_match(request, match_uuid):
    match = get_match_or_validate_judge_requests(request, match_uuid)
    execute_match(match)
    return redirectToCurrent(request);
