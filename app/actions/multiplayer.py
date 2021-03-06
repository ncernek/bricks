import traceback
from sqlalchemy import func
from app import db
from app.models import AppUser, Point, Exchange, Team, TeamMember
from app.constants import Statuses, Reserved
from app.actions import solo
from app import tools


def get_leaderboard(**kwargs):
    '''Make a leaderboard across all users, returning the top users'''
    users = db.session.query(AppUser.username, func.sum(Point.value))\
        .join(Point)\
        .group_by(AppUser.username)\
        .order_by(func.sum(Point.value).desc())\
        .limit(10)\
        .all()
    
    board = "{points:<8}{username}\n".format(username='USERNAME', points='POINTS')
    for user, value in users:
        board = board + "{value:<15}{user}\n".format(user=user[:16], value=value)

    return board


def get_team_leaderboard(user, **kwargs):
    '''Make a leaderboard for the teams you are on'''
    team_members = get_current_team_members(user, exclude_user=False)

    teams = dict()
    for member, team in team_members:
        if not  team.name in teams:
            teams[team.name] = list()
        # get points for member
        points = solo.get_total_points(member.to_dict())
        # add uname, points to team list
        teams[team.name].append((points, member.username))
    
    board = str()
    for team, user_list in teams.items():
        team_board = '\n' + team + str_leaderboard(user_list) + '\n'
        board += team_board

    return board


def str_leaderboard(user_list):
    '''sort users by points and return as a str'''
    user_list = sorted(user_list, reverse=True)
    board = str()
    for points, user in user_list:
        board = board + "\n{points:<15}{user}".format(points=points, user=user[:16])
    return board


def insert_team(user, inbound, **kwargs):
    '''Create a new team with the user as the founder, and the inbound as the team name. 
     add this user to this team in TeamMember'''
    team = Team(founder_id=user['id'], name=inbound)

    member = TeamMember(
        user_id=user['id'],
        team=team,
        inviter_id=user['id'],
        status=Statuses.ACTIVE)

    db.session.add(team)
    db.session.add(member)
    db.session.commit()

    print(f"USER {user['username']} CREATED TEAM {team.name}")


def insert_team_beta(user, name, **kwargs):
    '''Create a new team with the user as the founder. 
     add this user to this team in TeamMember'''
    team = Team(founder_id=user.id, name=name)

    member = TeamMember(
        user_id=user.id,
        team=team,
        inviter_id=user.id,
        status=Statuses.ACTIVE)

    db.session.add(team)
    db.session.add(member)
    db.session.commit()
    db.session.close()

    return team


def list_teams(user, **kwargs):
    '''List the teams that user is a member of'''
    teams = db.session.query(Team.id, Team.name).join(TeamMember)\
        .filter(
            TeamMember.user_id == user['id'],
            TeamMember.status == Statuses.ACTIVE).all()

    if teams:
        team_list = str()
        for team_id, name in teams:
            team_list += f"{team_id}: {name}\n"
        return team_list
    else:
        return "You have no teams. Return to the main menu and create one."


def get_open_teams(user, id_only=False, **kwargs):
    '''List teams that don't have 5 active members yet'''

    all_team_ids = db.session.query(Team.id).join(TeamMember.team)\
        .filter(TeamMember.user_id == user['id']).subquery()
    
    teams = db.session.query(Team.id, Team.name, func.count(TeamMember.team_id).label('size'))\
        .join(TeamMember.team)\
        .filter(
            Team.id.in_(all_team_ids),
            TeamMember.status == 'ACTIVE')\
        .group_by(Team).all()
    
    # filter out teams with 5 or more members
    if not teams:
        return None

    open_teams = list()
    for team in teams:
        if team.size < 5:
            if id_only:
                open_teams.append(team.id)
            else:
                open_teams.append(team)
    
    return open_teams


def str_open_teams(user, **kwargs):
    '''return open teams as a str'''
    teams = get_open_teams(user)
    if not teams:
        return "You have no open teams."
    team_list = str()
    for team_id, name, _ in teams:
        team_list += f"{team_id}: {name}\n"
    return team_list


def insert_member(user, inbound, init_onboarding_invited, you_were_invited, **kwargs):
    '''Add member to the given team as PENDING. 
    Inbound should already be parsed as tuple(team_id, phone_number_str)'''

    team_id, phone_number = inbound

    # confirm that user is part of team
    team = db.session.query(Team).join(TeamMember).filter(
        Team.id == team_id, 
        TeamMember.user_id == user['id'],
        TeamMember.status == Statuses.ACTIVE
    ).one()

    # confirm that this team is open
    open_team_ids = get_open_teams(user, id_only=True)
    assert team.id in open_team_ids

    # lookup the phone-number, add if not already a user
    invited_user = tools.query_user_with_number(phone_number)

    # insert invitee into db
    invited_member = TeamMember(
        user_id = invited_user['id'],
        team_id = team_id,
        inviter_id = user['id'],
        status = Statuses.PENDING)
    
    db.session.add(invited_member)
    db.session.commit()

    # send invitation to invitee
    # you need to get the right router
    # you should trigger a new router, but does that

    exchange = tools.query_last_exchange(invited_user)
    if exchange is None or invited_user['username'] == Reserved.NEW_USER:
        router = init_onboarding_invited()
    else:
        router = you_were_invited()

    results = router.run_pre_actions(
        user=invited_user,
        exchange=exchange,
        inviter=user)

    router.outbound = router.outbound.format(**results)

    tools.send_message(invited_user, router.outbound)

    # record the fact that this invitation was sent to a user
    tools.insert_exchange(router, invited_user)


def get_last_invitation(user, **kwargs):
    '''find the most recent invitation for user'''
    inviter_username, inviter_phone_number, team_name = db.session.query(AppUser.username, AppUser.phone_number, Team.name)\
        .join(TeamMember.inviter, TeamMember.team)\
        .filter(
            TeamMember.user_id == user['id'],
            TeamMember.status == Statuses.PENDING)\
        .order_by(TeamMember.created.desc()).first()

    return inviter_username, team_name, inviter_phone_number

# TODO(Nico) create this 
def intro_to_team(**kwargs):
    return "Me, You and Larry"


def notify_inviter(user, membership, **kwargs):
    '''look up which membership was just responded to, and notify the inviter'''
    # find the inviter
    inviter, team_name = db.session.query(AppUser, Team.name)\
        .join(TeamMember.inviter, TeamMember.team).filter(
            TeamMember.user_id == user['id'],
            TeamMember.inviter_id == membership.inviter_id,
            TeamMember.team_id == membership.team_id)\
        .order_by(TeamMember.updated.desc()).first()

    if membership.status == Statuses.ACTIVE:    
        outbound = "Your friend @{phone_number} just accepted your invitation to {team_name}."
    elif membership.status == Statuses.REJECTED:
        outbound = "Your friend @{phone_number} did not accept your invitation to {team_name}."
    elif membership.status == Statuses.PENDING: 
        return None
    
    outbound = outbound.format(phone_number=user['phone_number'], team_name=team_name)

    tools.send_message(inviter.to_dict(), outbound)


def respond_to_invite(user, inbound, **kwargs):
    '''set the membership being responded to, to ACTIVE or REJECTED'''
    membership = db.session.query(TeamMember).filter(
        TeamMember.user_id == user['id'],
        TeamMember.status == Statuses.PENDING)\
        .order_by(TeamMember.created.desc()).first()
    
    assert membership is not None
    
    if inbound in ['a', 'yes']:
        membership.status = Statuses.ACTIVE
        print("INVITATION CONFIRMED: ", user['phone_number'])
    elif inbound in ['b', 'no']:
        membership.status = Statuses.REJECTED
        print("INVITATION REJECTED BY: ", user['phone_number'])
    else:
        print('INVITEE IS TRYING TO UNDERSTAND INVITATION.')
    db.session.commit()

    return membership


def get_current_team_members(user, exclude_user=True, **kwargs):
    '''get the team members for this user. optionally exclude this user from the results.'''
    team_ids = db.session.query(Team.id).join(TeamMember)\
                .filter(
                    TeamMember.user_id == user['id'],
                    TeamMember.status == Statuses.ACTIVE).all()

    filters = [
            TeamMember.team_id.in_(team_ids),
            TeamMember.status == Statuses.ACTIVE]
    
    if exclude_user:
        filters.append(TeamMember.user_id != user['id'])

    team_members = db.session.query(AppUser, Team).join(TeamMember.user, TeamMember.team)\
        .filter(*filters).all()

    return team_members

def get_current_team_members_beta(user, exclude_user=True, **kwargs):
    '''get the team members for this user. optionally exclude this user from the results.'''
    team_ids = db.session.query(Team.id).join(TeamMember)\
                .filter(
                    TeamMember.user_id == user.id,
                    TeamMember.status == Statuses.ACTIVE).all()

    filters = [
            TeamMember.team_id.in_(team_ids),
            TeamMember.status == Statuses.ACTIVE]
    
    if exclude_user:
        filters.append(TeamMember.user_id != user.id)

    # TODO I removed the join on TeamMember.team because I don't yet care about team info
    team_members = db.session.query(AppUser).join(TeamMember.user)\
        .filter(*filters).distinct().all()

    return team_members


def notify_team_members(user, inbound, **kwargs):
    '''Send message to teammembers that user is doing inbound'''

    team_members = get_current_team_members(user)
    for team_member, team in team_members:
        outbound = f"Your friend {user['username']} is gonna do this: {inbound}."
        try:
            tools.send_message(team_member.to_dict(), outbound)
        except Exception as error:
            traceback.print_exc()
            continue


def get_phonenumber(user, **kwargs):
    inviter_username, team_name, inviter_phone_number = get_last_invitation(user)

    return inviter_phone_number


def str_all_teams(user, **kwargs):
    '''list all teams and corresponding members for user'''
    team_members = get_current_team_members(user)
    if not team_members:
        return "You have no team members. Invite some by going back to the main menu."

    teams = dict()
    for member, team in team_members:
        if not  team.name in teams:
            teams[team.name] = str()
        teams[team.name] += f"\n- {member.username}"
    
    all_teams = str()
    for key, value in teams.items():
        all_teams += "\n" + key + value 
    
    return all_teams

# TODO (Nico) reconcile this with the other function
def members_of_invited_team(user, **kwargs):
    '''get team members for team that user is invited to'''
    team_id = db.session.query(TeamMember.team_id).filter(
        TeamMember.user_id == user['id'],
        TeamMember.status == Statuses.PENDING)\
            .order_by(TeamMember.updated.desc()).first()
    
    team_members = db.session.query(AppUser)\
        .join(TeamMember.user)\
        .filter(TeamMember.team_id == team_id,
            TeamMember.status == Statuses.ACTIVE).all()
    
    return team_members


def str_members_of_invited_team(user, **kwargs):
    '''list team members of user for team as string'''
    team_members = members_of_invited_team(user)
    member_str = str()
    for member in team_members:
        member_str += '\n- ' + member.username
    
    return member_str


def leave_team(user, inbound, **kwargs):
    '''leave the team specified by inbound if the user is a part of it'''

    # check that user is part of team
    membership = db.session.query(TeamMember).filter(
        TeamMember.team_id == inbound,
        TeamMember.user_id == user['id'],
        TeamMember.status == Statuses.ACTIVE).one()
    
    membership.status = Statuses.LEFT

    db.session.commit()
    db.session.close()
