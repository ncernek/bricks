import datetime as dt
from flask import request, session
from twilio.twiml.messaging_response import MessagingResponse
from app import scheduler, db
from app.init_session import main as init_session
from app.parse_inbound import main as parse_inbound
from app.queries import insert_exchange, update_exchange
from app.routers import routers
from app.router_actions import ROUTER_ACTIONS
from app.condition_checkers import CONDITION_CHECKERS
from config import Config # TODO(Nico) access the config that has been initialized on the app 


def main():
    """Respond to SMS inbound with appropriate SMS outbound based on conversation state and response_db.py"""

    init_session(session, request)

    # gather relevant data from inbound request
    session['exchange']['inbound'] = request.values.get('Body')
    print(f"INBOUND FROM {session['user']['username']}: {session['exchange']['inbound']}")

    # parse inbound based on match on router_id
    parsed_inbound = parse_inbound(session['exchange']['inbound'], session['exchange']['router_id'])

    # execute all actions defined on the router
    result_dict = execute_actions(
        session['exchange']['actions'], 
        session['exchange']['router_id'], 
        parsed_inbound, 
        session['user'])

    # decide on next router, including outbound and actions
    next_router = select_next_router(
        session, 
        parsed_inbound, 
        session['user'])
    
    # update current exchange in DB with inbound and next router
    update_exchange(
        session['exchange']['id'], 
        session['exchange']['inbound'],
        next_router['router_id'])

    # format next router outbound with result_dict
    next_router['outbound'].format(**result_dict)

    # insert the next router into db as an exchange
    next_exchange = insert_exchange(
        next_router, 
        session['user'])

    # save values to persist in session so that we know how to act on user's response to our outbound
    session['exchange'] = next_exchange

    # send outbound    
    resp = MessagingResponse()
    resp.message(next_router['outbound'])
    return str(resp)


def execute_actions(actions, last_router_id, inbound, user):
    if inbound is not None and actions is not None:
        result_dict = dict()
        for action_name in actions:
            action_func = ROUTER_ACTIONS[action_name]

            result = action_func(
                last_router_id=last_router_id, 
                inbound=inbound, 
                user=user)
            print('ACTION EXECUTED: ', action_name)

            result_dict[action_name] = result

        return result_dict
    return None


def select_next_router(session, inbound, user):
    '''Query the static router table to find the right outbound message and action'''

    if inbound is None:
        # resend the same router
        RETRY = "Your response is not valid, try again.\n"
        session['exchange']['outbound'] = RETRY + session['exchange']['outbound']

        return session['exchange']

    # find all routers that can branch from the current router & that interact with the inbound
    filtered = routers[
        (routers.last_router_id == session['exchange']['router_id']) & 
        (
            (routers.inbound == inbound) |  
            (routers.inbound == '*')
    )]
    
    if len(filtered) == 1:
        router = filtered.iloc[0]
    elif len(filtered) == 0:
        # redirect to the main menu
        router = routers[routers.router_id == 'main_menu'].iloc[0]
        router['outbound'] = "Can't interpret that; sending you to the menu.\n" + router['outbound']
    else:
        # match on a condition
        matches = 0
        for i, (checker, expected_value) in enumerate(filtered['condition']):
            checker_func = CONDITION_CHECKERS[checker]
            if checker_func(user) == expected_value:
                router = filtered.iloc[i]
                matches += 1
        if matches > 1:
            raise NotImplementedError("The routers are ambiguous - too many matches. fix your routers.")
        elif matches == 0:
            raise NotImplementedError("The routers are ambiguous - no match for this condition. fix your routers.")
    
    # append last router's confirmation to next router's outbound
    if  session['exchange']['confirmation'] is not None:
        router['outbound'] = session['exchange']['confirmation'] + " " + router['outbound']

    return router
