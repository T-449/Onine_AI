from django.urls import path
from . import views

urlpatterns = [
    path('create', views.create_tournament, name='show_tournament_creator_page'),
    path('post/create_tournament', views.post_create_tournament, name='post_create_tournament'),

    path('<uuid:tournament_uuid>/update', views.update_tournament, name='update_tournament'),
    path('<uuid:tournament_uuid>/post/update_tournament', views.post_update_tournament, name='post_update_tournament'),

    path('<uuid:tournament_uuid>', views.show_tournament_workspace, name='show_tournament_workspace'),
    path('<uuid:tournament_uuid>/register', views.reg_unreg, name='register_tournament'),
    path('tournamentList', views.tournamentList, name='tournamentList'),
    path('<uuid:tournament_uuid>/submission', views.add_submission, name='add_submission'),
    path('<uuid:tournament_uuid>/phasechange', views.change_phase, name='change_phase'),
    path('<uuid:tournament_uuid>/create_test_match', views.tournament_post_create_test_match,
         name='tournament_post_create_test_match'),

]