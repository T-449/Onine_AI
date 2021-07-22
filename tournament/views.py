import traceback
from datetime import datetime

from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404

from django.urls import reverse
from django.utils import timezone
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.utils.timezone import get_default_timezone, get_current_timezone, make_aware

from Online_AI import settings
from Online_AI.settings import MAX_TEST_GENERATION_LIMIT
from game_creator.models import Game, GameCreatorWorkspaceACL
from match.models import Match, TournamentTestMatchTable, TournamentMatchTable
from match_generator.round_robin_match_generator import RoundRobinMatchGenerator
from myutils.fileutils import get_file_content_as_string
from ranklist.victory_count_rank_generator import VictoryCountRankGenerator
from tournament.models import Tournament, TournamentCreatorACL, TournamentRegistration
from submission.models import Submission, TournamentSubmissionEntry, WorkspaceTestSubmissionEntry
from itertools import chain


# Create your views here.

@login_required
def create_tournament(request):
    games = GameCreatorWorkspaceACL.objects.filter(user_id=request.user.id)
    gameList = []
    for game in games:
        gameList.append(game.game)
    tournament_types = Tournament.TournamentType.names

    context = {
        'games': gameList,
        'tournament_types': tournament_types,
        'servertime': timezone.now(),
        'MAX_TEST_GENERATION_LIMIT': MAX_TEST_GENERATION_LIMIT
    }
    return render(request, 'tournament/createTournament.html', context)


@login_required
def update_tournament(request, tournament_uuid):
    tournament = Tournament.objects.get(tournament_uuid=tournament_uuid)
    games = GameCreatorWorkspaceACL.objects.filter(user_id=request.user.id)
    gameList = []
    for game in games:
        gameList.append(game.game)
    tournament_types = Tournament.TournamentType.names

    context = {
        'tournament': tournament,
        'games': gameList,
        'tournament_types': tournament_types,
        'servertime': timezone.now(),
        'MAX_TEST_GENERATION_LIMIT': MAX_TEST_GENERATION_LIMIT
    }
    return render(request, 'tournament/updateTournament.html', context)


@login_required
def post_create_tournament(request):
    givendate = request.POST['startdate'].split('-')
    giventime = request.POST['starttime'].split(':')
    start_time = datetime(int(givendate[0]), int(givendate[1]), int(givendate[2]),
                          int(giventime[0]), int(giventime[1]), int(giventime[2]), 0)
    start_time = make_aware(start_time)

    givendate = request.POST['enddate'].split('-')
    giventime = request.POST['endtime'].split(':')
    end_time = datetime(int(givendate[0]), int(givendate[1]), int(givendate[2]),
                        int(giventime[0]), int(giventime[1]), int(giventime[2]), 0)
    end_time = make_aware(end_time)
    game_id = request.POST['game']

    game = Game.objects.get(pk=game_id)
    user = request.user

    try:
        tournament = Tournament.objects.create_tournament(creator=user, name=request.POST['tournamentname'], game=game,
                                                          start_time=start_time, end_time=end_time,
                                                          description=request.POST['description'],
                                                          phase=Tournament.TournamentPhase.OPEN_FOR_REGISTRATION,
                                                          tournament_type=Tournament.TournamentType[
                                                              request.POST['tournamentType']],
                                                          max_match_generation_limit=int(request.POST['maxMatches']))
    except Exception as e:
        traceback.print_exc(e)
        return HttpResponseRedirect(reverse('tournamentList'))
    return HttpResponseRedirect(reverse('show_tournament_workspace', args=(tournament.tournament_uuid,)))


def post_update_tournament(request, tournament_uuid):
    givendate = request.POST['startdate'].split('-')
    giventime = request.POST['starttime'].split(':')
    start_time = datetime(int(givendate[0]), int(givendate[1]), int(givendate[2]),
                          int(giventime[0]), int(giventime[1]), int(giventime[2]), 0)
    start_time = make_aware(start_time)

    givendate = request.POST['enddate'].split('-')
    giventime = request.POST['endtime'].split(':')
    end_time = datetime(int(givendate[0]), int(givendate[1]), int(givendate[2]),
                        int(giventime[0]), int(giventime[1]), int(giventime[2]), 0)
    end_time = make_aware(end_time)

    game_id = request.POST['game']
    game = Game.objects.get(pk=game_id)

    tournament = Tournament.objects.get(tournament_uuid=tournament_uuid)
    try:
        tournament.name = request.POST['tournamentname']
        tournament.game = game
        tournament.start_time = start_time
        tournament.end_time = end_time
        tournament.type = request.POST['tournamentType']
        tournament.max_match_generation_limit = int(request.POST['maxMatches'])
        tournament.save()
    except Exception as e:
        traceback.print_exc(e)
        HttpResponseRedirect(reverse('tournamentList'))
    return HttpResponseRedirect(reverse('show_tournament_workspace', args=(tournament.tournament_uuid,)))


def show_tournament_workspace(request, tournament_uuid):
    tournament = Tournament.objects.get(tournament_uuid=tournament_uuid)
    game = tournament.game
    game_description = get_file_content_as_string(game.get_game_description_filepath()).encode('unicode_escape'
                                                                                               ).decode('utf-8')

    #VictoryCountRankGenerator(tournament).generate_ranklist()

    visible = True
    registered = False
    if request.user.id is not None:
        if TournamentCreatorACL.objects.filter(user=request.user, tournament=tournament).exists():
            visible = False
        else:
            if TournamentRegistration.objects.filter(user=request.user,
                                                     tournament=tournament).exists():
                registered = True
    else:
        visible = False
    test_agents = WorkspaceTestSubmissionEntry.objects.filter(game=game, is_test=True).values_list('submission',
                                                                                                   flat=True)
    tournament_test_matches = []
    user_submissions = []
    submissions = []
    if request.user.is_authenticated:
        tournament_test_matches = TournamentTestMatchTable.objects.filter(user=request.user, tournament=tournament)
        user_submissions = TournamentSubmissionEntry.objects.filter(tournament=tournament,
                                                                    submission__user=request.user).values_list(
            'submission',
            flat=True)
        submissions = TournamentSubmissionEntry.objects.all().filter(submission__user=request.user)

    submission_list_pk = list(chain(test_agents, user_submissions))

    submission_list = []
    for pk in submission_list_pk:
        submission_list.append(Submission.objects.get(pk=pk))

    generatedMatches = []

    if tournament.phase == Tournament.TournamentPhase.MATCH_EXECUTION:
        generatedMatches = TournamentMatchTable.objects.filter(tournament=tournament)

    return render(request, 'tournament/tournament_tabs.html',
                  {'tournament': tournament, 'game': game.game_title, 'visible': visible, 'registered': registered,
                   'tournament_test_matches': tournament_test_matches, 'game_description': game_description,
                   'entries': submissions, 'testEntries': submission_list,
                   'tournamentPhases': Tournament.TournamentPhase, 'matchEntries': generatedMatches})


@login_required
def reg_unreg(request, tournament_uuid):
    val = request.POST['register']
    val = val.split()
    tournament = Tournament.objects.get(tournament_uuid=tournament_uuid)
    user = request.user

    r = HttpResponseRedirect(reverse('tournamentList'))

    if tournament.phase != Tournament.TournamentPhase.OPEN_FOR_REGISTRATION:
        print("User ", user, " is trying to register")
        messages.error(request, "Registration time is over")
        return r

    if val[0] == 'reg':
        try:
            TournamentRegistration.objects.get(user=user, tournament=tournament)
        except:
            TournamentRegistration(user=user, tournament=tournament).save()
    else:
        try:
            TournamentRegistration.objects.get(tournament=tournament, user=user).delete()
        except Exception as e:
            traceback.print_exc(limit=None)
    return HttpResponseRedirect(reverse('show_tournament_workspace', args=(tournament_uuid,)))


def tournamentList(request):
    tournaments = Tournament.objects.all()
    tournament_phases = Tournament.TournamentPhase.names
    myTournaments = TournamentCreatorACL.objects.filter(user_id=request.user.id)
    myTournamentList = []
    for tournament in myTournaments:
        myTournamentList.append(Tournament.objects.get(id=tournament.tournament_id))
    registeredTournaments = TournamentRegistration.objects.filter(user_id=request.user.id)
    registeredTournamentList = []
    for tournament in registeredTournaments:
        registeredTournamentList.append(Tournament.objects.get(id=tournament.tournament_id))
    show = False
    if request.user.id is not None:
        show = True
    return render(request, 'tournament/tournamentList.html',
                  {'tournaments': tournaments, 'show': show, 'myTournaments': myTournamentList,
                   'registeredTournaments': registeredTournamentList, 'tournament_phases': tournament_phases})


@login_required
def add_submission(request, tournament_uuid):
    tournament = Tournament.objects.get(tournament_uuid=tournament_uuid)
    r = HttpResponseRedirect(reverse('show_tournament_workspace', args=(tournament_uuid,)))

    if tournament.phase != Tournament.TournamentPhase.OPEN_FOR_SUBMISSION:
        print("submission out of phase")
        messages.error(request, "Submission window has been closed")
        return r

    try:
        TournamentRegistration.objects.get(tournament=tournament, user=request.user)
    except:
        print("unregistered user ", request.user, " trying to submit code in tournament ", tournament)
        messages.error(request, "You are not Registered For this tournament")
        return r

    Submission.objects.create_tournament_submission(user=request.user,
                                                    code=request.POST['submission_code'],
                                                    language=request.POST['submission_language'],
                                                    tournament=tournament,
                                                    time=timezone.now())
    messages.success(request, "Saved")
    return show_tournament_workspace(request, tournament_uuid)


def change_phase(request, tournament_uuid):
    tournament = Tournament.objects.get(tournament_uuid=tournament_uuid)
    print(tournament.TournamentPhase.choices)
    print(tournament.TournamentPhase.values)
    print(tournament.TournamentPhase.names)
    print(tournament.TournamentPhase['OPEN_FOR_REGISTRATION'])

    try:
        tournament.phase = Tournament.TournamentPhase[request.POST['changedphase']]
        tournament.save()

        if tournament.phase == Tournament.TournamentPhase.MATCH_EXECUTION:
            matchGenerator = RoundRobinMatchGenerator(tournament)
            matchGenerator.run()
    except Exception as e:
        traceback.print_exc(e)

    return HttpResponseRedirect(reverse('show_tournament_workspace', args=(tournament_uuid,)))


@login_required
def tournament_post_create_test_match(request, tournament_uuid):
    tournament = get_object_or_404(Tournament, tournament_uuid=tournament_uuid)
    game = tournament.game

    r = HttpResponseRedirect(reverse('show_tournament_workspace', args=(tournament_uuid,)))

    if tournament.phase != Tournament.TournamentPhase.OPEN_FOR_SUBMISSION:
        print("test match creation is out of phase")
        messages.error(request, "Submission window has been closed")
        return r

    try:
        TournamentRegistration.objects.get(tournament=tournament, user=request.user)
    except:
        print("unregistered user ", request.user, " trying to create  test match in tournament ", tournament)
        messages.error(request, "You are not Registered For this tournament")
        return r

    user_matches = TournamentTestMatchTable.objects.filter(tournament=tournament, user=request.user)
    print(user_matches, len(user_matches), tournament.max_match_generation_limit)
    if len(user_matches) >= tournament.max_match_generation_limit:
        print("user ", request.user, " has already created ", len(user_matches), " match; max_limit: ",
              tournament.max_match_generation_limit)
        messages.error(request, "You can not create any more matches")
        return r

    user_submissions = TournamentSubmissionEntry.objects.filter(tournament=tournament,
                                                                submission__user=request.user).values_list('submission',
                                                                                                           flat=True)
    test_agents = WorkspaceTestSubmissionEntry.objects.filter(game=game, is_test=True).values_list('submission',
                                                                                                   flat=True)
    try:
        submission0 = Submission.objects.get(submission_uuid=request.POST['submission0'].strip())
        submission1 = Submission.objects.get(submission_uuid=request.POST['submission1'].strip())
    except:
        print("User ", request.user, " making invalid submission")
        messages.error(request, "Invalid Submission")
        return r

    if submission0.pk not in user_submissions and submission0.pk not in test_agents:
        print(submission0)
        print(user_submissions)
        print(test_agents)
        print("User ", request.user, " making invalid submission")
        messages.error(request, "Invalid Submission")
        return r

    if submission1.pk not in user_submissions and submission1.pk not in test_agents:
        print(submission0)
        print(user_submissions)
        print(test_agents)
        print("User ", request.user, " making invalid submission")
        messages.error(request, "Invalid Submission")
        return r

    Match.objects.create_tournament_test_match(submission0=submission0, submission1=submission1,
                                               tournament=tournament, user=request.user)
    return r
