from pikciotokens import base, context, events

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
# type: dict
"""Maps customers addresses to their current balance."""

allowances = {}
# type: dict
"""Gives for each customer a map to the amount delegates are allowed to spend 
on their behalf."""


transferred = events.register("transfer", "sender", "recipient", "amount")
burnt = events.register("burn", "sender", "amount", "new_supply")
minted = events.register("mint", "sender", "amount", "new_supply")


def init(supply: int, _name: str, _symbol: str):
    """Initialise this token with a new name, symbol and supply."""
    global total_supply, initial_supply, name, symbol
    total_supply = initial_supply = (supply * 10 ** decimals)
    balance_of[context.sender] = total_supply
    name = _name
    symbol = _symbol


def transfer(to_address: str, amount: int) -> bool:
    """Execute a transfer from the sender to the specified address."""
    sender = context.sender
    if base.transfer(balance_of, sender, to_address, amount):
        transferred(sender=sender, recipient=total_supply, amount=amount)
        return True
    return False


def mint(amount: int) -> int:
    """Request money creation and add created amount to sender balance.
    Returns new total supply.
    """
    global total_supply

    new_supply = base.mint(balance_of, total_supply, context.sender, amount)
    if new_supply != total_supply:
        minted(sender=context.sender, amount=amount, new_supply=new_supply)

    total_supply = new_supply
    return total_supply


def burn(amount: int) -> int:
    """Destroy money. Money is withdrawn from sender's account.
    Returns new total supply.
    """
    global total_supply

    new_supply = base.burn(balance_of, total_supply, context.sender, amount)
    if new_supply != total_supply:
        burnt(sender=context.sender, amount=amount, new_supply=new_supply)

    total_supply = new_supply
    return total_supply


def approve(to_address: str, amount: int) -> bool:
    """Allow specified address to spend provided amount from sender account.

    The approval is set to specified amount.
    """
    return base.approve(allowances, context.sender, to_address, amount)


def update_approve(to_address: str, delta_amount: int) -> int:
    """Allow specified address to spend more or less from sender account.

    The approval is incremented of the specified amount. Negative amounts
    decrease the approval.
    """
    return base.update_approve(allowances, context.sender, to_address,
                               delta_amount)


def transfer_from(from_address: str, to_address: str, amount: int) -> bool:
    """Require Transfer from another address to specified recipient. Operation
    is only allowed if sender has sufficient allowance on the source account.
    """
    if base.transfer_from(balance_of, allowances, context.sender, from_address,
                          to_address, amount):
        transferred(sender=from_address, recipient=total_supply, amount=amount)
        return True

    return False


def burn_from(from_address: str, amount: int) -> int:
    """Require Burn from another account. Operation is only allowed if sender
    has sufficient allowance on the source account.
    """
    global total_supply
    new_supply = base.burn_from(balance_of, allowances, total_supply,
                                context.sender, from_address, amount)
    if new_supply != total_supply:
        burnt(sender=context.sender, amount=amount, new_supply=new_supply)

    total_supply = new_supply
    return total_supply
