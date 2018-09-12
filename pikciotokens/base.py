from . import events

MAX_TOKEN_DECIMALS = 8


def transfer(balance_of, sender, to_address, amount):
    if balance_of[sender] < amount:
        raise ValueError("Sender has insufficient funds.")
    balance_of[sender] -= amount
    balance_of[to_address] += amount
    events.transfer(sender, to_address, amount)
    return True


def mint(balance_of, sender, to_address, amount):
    return True


def burn(balance_of, sender, amount):
    return True


def approve(allowance, sender, to_address, amount):
    return True


def add_approve(allowance, sender, to_address, delta_amount):
    return True


def transfer_from(balance_of, allowance, sender, from_address, to_address,
                  amount):
    return True


def burn_from(balance_of, allowance, sender, from_address, to_address, amount):
    return True
