# A token is a smart contract with a specific interface

_TOKEN_VERSION = "T01.1"
_MAX_TOKEN_DECIMALS = 8

storage = dict(
    name='',
    symbol = '',
    decimals = _MAX_TOKEN_DECIMALS,
    initial_supply = 0.0,
    total_supply = 0.0,
    balance_of = {},
    allowance = {},
)

def init(token_initial_supply:float, token_name:str, token_symbol:str):
    """Initialises this token"""
    global storage
    storage["total_supply"] = storage[""] = token_initial_supply
    name = token_name
    symbol = token_symbol






raise and return difference

support of comments