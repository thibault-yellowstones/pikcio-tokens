# A token is a smart contract with a specific interface

from pikciotokens import base

_TOKEN_VERSION = "T01.1"

name = ''
"""The friendly name of the token"""

symbol = ''
"""The symbol of the token currency. Should be 3 or 4 characters long."""

decimals = base.MAX_TOKEN_DECIMALS
"""Maximum number of decimals to express any amount of that token."""

initial_supply = 0
"""The initial amount of the token on the market."""

total_supply = 0
"""The current amount of the token on the market, in case some has been minted 
or burnt."""

balance_of = {}
# type: dict[str,int]
"""Maps customers addresses to their current balance."""

allowance = {}
# type: dict[str,dict[str,int]]
"""Gives for each customer a map to the amount spenders are allowed to spend 
on his behalf."""


def init(context: base.Context, token_initial_supply: float, token_name: str,
         token_symbol: str):
    """Initialises this token

    :param context:
    :param token_initial_supply:
    :param token_name:
    :param token_symbol:
    :return:
    """
    global total_supply, initial_supply, name, symbol
    total_supply = initial_supply = (token_initial_supply * 10 ** decimals)
    balance_of[context.sender] = total_supply
    name = token_name
    symbol = token_symbol


def transfer(context: base.Context, to_address: str, amount: int):
    """

    :param context:
    :param to_address:
    :param amount:
    :return:
    """
    return base.transfer(balance_of, context.sender, to_address, amount)


def mint(context: base.Context, to_address: str, amount: int):
    """

    :param context:
    :param to_address:
    :param amount:
    :return:
    """
    return base.mint(balance_of, context.sender, to_address, amount)


def burn(context: base.Context, to_address: str, amount: int):
    """

    :param context:
    :param to_address:
    :param amount:
    :return:
    """
    return base.burn(balance_of, context.sender, to_address, amount)


def approve(context: base.Context, to_address: str, amount: int):
    pass


def transfer_from(context: base.Context, to_address: str, amount: int):
    """

    :param context:
    :param to_address:
    :param amount:
    :return:
    """
    return base.transfer(balance_of, context.sender, to_address, amount)


def burn_from(context: base.Context, to_address: str, amount: int):
    """

    :param context:
    :param to_address:
    :param amount:
    :return:
    """
    return base.transfer(balance_of, context.sender, to_address, amount)
