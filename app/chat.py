import os
import traceback
from flask import request, current_app
from twilio.twiml.messaging_response import MessagingResponse
from app import tools
from app.get_router import get_router
from app.routers import InitOnboarding, MainMenu
from app.constants import Outbounds, Redirects


def main():
    """Respond to SMS inbound with appropriate SMS outbound based on last exchange"""
    
    ACTION_ERROR = False

    inbound = request.values.get('Body')
    if inbound is None:
        return f"Please use a phone and text {os.environ.get('TWILIO_PHONE_NUMBER')}. This does not work thru the browser."

    user = tools.query_user_with_number(request.values.get('From'))
    print("USER: ", user['username'])
    exchange = tools.query_last_exchange(user)

    if exchange is None:
        router = InitOnboarding()
    else:
        router = get_router(exchange['router'])()
    print("ROUTER: ", router.name)

    parsed_inbound = router.parse(inbound)

    if parsed_inbound == Redirects.MAIN_MENU:
        # send the user to the main menu
        next_router = MainMenu()
        action_results = dict()

    elif parsed_inbound is not None:

        # give participation points
        points_message = router.insert_points(user=user, inbound=parsed_inbound)

        # execute current exchange actions after getting inbound
        # this needs to run before selecting the next router, as 
        # these actions can influence the next router choice
        try:
            action_results = router.run_actions(
                user=user,
                exchange=exchange,
                inbound=parsed_inbound)

            # decide on next router, including outbound and actions
            next_router = router.next_router(
                inbound=parsed_inbound,
                user=user,
                action_results=action_results)()
            
            # append last router's confirmation to next router's outbound
            if  router.confirmation is not None:
                next_router.outbound = router.confirmation + " " + next_router.outbound
            
            # prepend points message
            next_router.outbound = points_message + " " + next_router.outbound
        
        except Exception as error: # if there was an error in the action then resend the same router
            traceback.print_exc()
            ACTION_ERROR = True
            # throw error if in testing mode
            # TODO(Nico) there is probably a cleaner way to do this
            if current_app.config['TESTING'] == True:
                raise error
        
    if (parsed_inbound is None) or ACTION_ERROR:
        # resend the same router
        action_results = dict()
        next_router = router
        # prepend a string to the outbound saying you need to try again
        next_router.outbound = Outbounds.RETRY + next_router.outbound

    print("NEXT ROUTER: ", next_router.name)
    # run the pre-actions for next router before sending the outbound message
    pre_action_results = next_router.run_pre_actions(
        user=user,
        exchange=exchange)

    # combine all action results and add them to next router's outbound message
    results = {**action_results, **pre_action_results}
    next_router.outbound = next_router.outbound.format(**results) # TODO do I want to mutate this?

    # insert the next router into db as the next exchange
    next_exchange = tools.insert_exchange(next_router, user)

    # update current exchange in DB with inbound and next exchange info
    tools.update_exchange(exchange, next_exchange, parsed_inbound)

    # send outbound    
    resp = MessagingResponse()
    resp.message(next_exchange['outbound'])
    return str(resp)
