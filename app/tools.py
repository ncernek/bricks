import functools
from app.models import ConvoHistory
from app.base_init import init_app, init_db


def with_app_context(func):
    '''inits a new app and db, and runs func within it. used for functions run by scheduler'''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        app = init_app()
        db = init_db(app)
        kwargs['db'] = db
        with app.app_context():
            return func(*args, **kwargs)
    return wrapper


# TODO(Nico) you can make log_convo into a decorator too
@with_app_context
def log_convo(router_id, inbound, outbound, user, db=None):
    '''log all elements of convo to db'''

    # this is implemented as such so that calling log_convo still requires db via the decorator  
    assert db is not None, 'You must provide a db instance'

    convo = ConvoHistory(
        router_id=router_id,
        inbound=inbound,
        outbound=outbound,
        user_id=user['id'])

    db.session.add(convo)
    db.session.commit()

    print('CONVO LOGGED ', convo)