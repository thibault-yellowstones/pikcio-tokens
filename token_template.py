from pikciotokens import base, context

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
on their behalf."""


def init(supply: float, _name: str, _symbol: str):
    """Initialise this token with a new name, symbol and supply."""
    global total_supply, initial_supply, name, symbol
    total_supply = initial_supply = (supply * 10 ** decimals)
    balance_of[context.sender] = total_supply
    name = _name
    symbol = _symbol


def transfer(to_address: str, amount: int) -> bool:
    """Execute a transfer from the sender to the specified address."""
    return base.transfer(balance_of, context.sender, to_address, amount)


def mint(to_address: str, amount: int) -> bool:
    """Request money creation and add created amount to recipient balance."""
    return base.mint(balance_of, context.sender, to_address, amount)


def burn(amount: int) -> bool:
    """Destroy money. Money is withdrawn from sender's account"""
    return base.burn(balance_of, context.sender, amount)


def approve(to_address: str, amount: int) -> bool:
    """Allow specified address to spend provided amount from sender account.

    The approval is set to specified amount.
    """
    return base.approve(allowance, context.sender, to_address, amount)


def add_approve(to_address: str, delta_amount: int) -> bool:
    """Allow specified address to spend more or less from sender account.

    The approval is incremented of the specified amount. Negative amounts
    decrease the approval.
    """
    return base.add_approve(allowance, context.sender, to_address,
                            delta_amount)


def transfer_from(from_address: str, to_address: str, amount: int) -> bool:
    """Require Transfer from another address to specified recipient. Operation
    is only allowed if sender has sufficient allowance on the source account.
    """
    return base.transfer_from(balance_of, allowance, context.sender,
                              from_address, to_address, amount)


def burn_from(from_address: str, to_address: str, amount: int) -> bool:
    """Require Burn from another account. Operation is only allowed if sender
    has sufficient allowance on the source account.
    """
    return base.burn_from(balance_of, allowance, context.sender, from_address,
                          to_address, amount)