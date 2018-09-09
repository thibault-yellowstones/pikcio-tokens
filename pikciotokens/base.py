from collections import namedtuple
from . import events

MAX_TOKEN_DECIMALS = 8

Context = namedtuple('Context', 'sender')


def transfer(balance_of, context, to_address, amount):
    if balance_of[context.sender] < amount:
        raise ValueError("Sender has insufficient funds.")
    balance_of[to_address] += amount
    events.transfer(context.sender, to_address, amount)
    return True
