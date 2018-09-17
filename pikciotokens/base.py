from functools import partial

from . import events

MAX_TOKEN_DECIMALS = 8
"""Define the default number of decimals of a token."""

missing_balance_means_zero = True
"""Indicate if semantically having no balance has the same meaning as having
an empty balance. Setting this to True allows some optimisations but loses some
meaning.
Depending on your need, change this attribute to affect default behavior of 
Balances and Allowances classes.
"""
zero_allowance_allows_transfer = False
"""Indicate if an allowance of 0 allows transfers of 0. Depends on your
business needs."""


def assert_positive_amount(amount):
    """Check that provided amount is positive. Raise an Exception otherwise.

    :param amount: The amount to check.
    :type amount: int
    """
    if amount < 0:
        raise ValueError("Negative amounts ({}) are forbidden.".format(amount))


def delete_entry_if_falsy(dct, key):
    """Delete entry at key in dict if entry is falsy (0, None, empty).

    :param dct: The dictionary to update.
    :type dct: dict
    :param key: The key to look for entry.
    """
    if not dct[key]:
        del dct[key]


class Balances(object):
    """Provide an object oriented interface to handle balances.

    The class updates the provided raw dictionary on your behalf.
    """

    def __init__(self, balance_of, missing_means_zero=None):
        """Create a new Balances object to wrap provided raw balances.

        :param balance_of: The raw balance, as a dict mapping accounts to
            amounts.
        :type balance_of: dict
        :param missing_means_zero: If True, indicates that an empty balance is
            equivalent to no balance. Allows optimisations. Default is set to
            missing_balance_means_zero module attribute.
        :type missing_means_zero: bool
        """
        self.balance = balance_of

        # Resolve args.
        if missing_means_zero is None:
            missing_means_zero = missing_balance_means_zero

        # Apply Strategy pattern:
        if missing_means_zero:
            # That means that empty accounts are in fact 0
            self._default_balance = 0
            # and that we can delete empty account for memory gain.
            self._post_withdraw = partial(delete_entry_if_falsy, self.balance)
        else:
            # Empty account is different than a 0 balance.
            self._default_balance = None
            # Never delete empty account.
            self._post_withdraw = lambda account: None

    def require(self, account, amount):
        """Check balance of an account against amount.

        Raise an Exception if balance is too low.
        :param account: Account to be checked.
        :type account: str
        :param amount: The amount to check.
        :type amount: int
        """
        # In that case, an empty account or a missing account behave the same.
        if self.balance.get(account, 0) < amount:
            raise ValueError(
                "Account {} has insufficient funds ({}<{}).".format(
                    account, self.balance.get(account, 0), amount
                ))

    def clear(self, account):
        """Delete provided account.

        :param account: The account to remove.
        :type account: str
        """
        del self.balance[account]

    def get(self, account):
        """Get the current balance of the provided account.

        :param account: The account to check.
        :type account: str
        :return: The current balance of the account, 0 or None if the account
            is missing, depending on the configuration.
        :rtype: int|None
        """
        return self.balance.get(account, self._default_balance)

    def deposit(self, account, amount):
        """Increase balance of an account of specified amount.

        A balance entry is created if it does not exists.

        :param account: Target account account.
        :type account: str
        :param amount: The amount to add.
        :type amount: int
        :return: The new balance of the account.
        :rtype: int
        """
        assert_positive_amount(amount)
        self.balance[account] = self.balance.get(account, 0) + amount
        return self.balance[account]

    def withdraw(self, account, amount):
        """Decrease balance of an account of specified amount.

        :param account: Address of the account.
        :type account: str
        :param amount: The amount to remove.
        :type amount: int
        :return: The new balance of the sender.
        :rtype: int
        """
        assert_positive_amount(amount)
        self.require(account, amount)
        self.balance[account] -= amount
        new_balance = self.balance[account]
        self._post_withdraw(account)
        return new_balance


class Allowances(object):
    """Provide an object oriented interface to handle spending allowances.

    The class updates the provided raw dictionary on your behalf.
    """

    def __init__(self, allowances, missing_means_zero=None,
                 zero_allowance_ok=None):
        """Create a new Allowances object to wrap provided raw allowances.

        :param allowances: the raw dictionary mapping accounts to all the
            delegations (account, amount) they allow.
        :type allowances: dict[str,dict[str,int]]
        :param missing_means_zero: If True, indicates that an empty allowance
            is equivalent to no allowance. Allows optimisations. Default is set
            to missing_balance_means_zero module attribute.
        :type missing_means_zero: bool
        :param zero_allowance_ok: If True, indicates that an empty allowance
            allows transfer of an empty amount. Default is set
            to zero_allowance_allows_transfer module attribute.
        :type zero_allowance_ok: bool
        """
        self.allowances = allowances

        # Resolve args
        if missing_means_zero is None:
            missing_means_zero = missing_balance_means_zero
        if zero_allowance_ok is None:
            zero_allowance_ok = zero_allowance_allows_transfer

        # Apply Strategy pattern:
        if missing_means_zero:
            # That means that empty allowances are in fact 0
            self._default_allowance = 0
            # and that we can delete empty allowances for memory gain.
            self._post_decrease = self._post_decrease_remove_entries_if_falsy
        else:
            # Empty allowance is different than a 0 allowance.
            self._default_balance = None
            # Never delete empty allowance.
            self._post_decrease = lambda account, delegate: None

        # Also branch authorisation strategy.
        self._allow_transfer = (
            self._allow_transfer_zero_allowed if zero_allowance_ok else
            self._allow_transfer_zero_not_allowed
        )

    @staticmethod
    def _allow_transfer_zero_allowed(allowance, amount):
        """Allow transfers if allowance <= amount."""
        return allowance is not None and allowance >= amount

    @staticmethod
    def _allow_transfer_zero_not_allowed(allowance, amount):
        """Allow transfers if 0 < allowance <= amount."""
        return allowance and allowance >= amount

    def _post_decrease_remove_entries_if_falsy(self, account, delegate):
        """Delete empty allowance entries related to account and delegate."""
        delete_entry_if_falsy(self.allowances[account], delegate)
        delete_entry_if_falsy(self.allowances, account)

    def get_all(self, account):
        """Get all the allowances of specified account."""
        return self.allowances.get(account, {})

    def get_one(self, account, delegate):
        """Get the allowance of a delegate on specified account."""
        return self.get_all(account).get(delegate, self._default_allowance)

    def require(self, account, delegate, amount):
        """Check allowance of delegate on behalf of account.

        Raise an Exception if allowance is too low.

        :param account: Address of the account allowing spending.
        :type account: str
        :param delegate: Address of the account allowed to spend.
        :type delegate: str
        :param amount: The amount to check.
        :type amount: int
        """
        if not self._allow_transfer(self.get_one(account, delegate), amount):
            raise ValueError("{} has not enough approval to spend {} on "
                             "behalf of {}".format(delegate, amount, account))

    def decrease(self, account, delegate, amount):
        """Decrease allowance of delegate on behalf of account.

        :param account: Address of the account allowing spending.
        :type account: str
        :param delegate: Address of the account allowed to spend.
        :type delegate: str
        :param amount: The amount to remove.
        :type amount: int
        :return: The new allowance of the delegate on behalf of the account.
        :rtype: int
        """
        assert_positive_amount(amount)
        # Allowance can't go below 0.
        new_allowance = max(0, self.get_one(account, delegate) - amount)
        self.set(account, delegate, new_allowance)
        self._post_decrease(account, delegate)
        return new_allowance

    def increase(self, account, delegate, amount):
        """Increase allowance of delegate on behalf of account.

        :param account: Address of the account allowing spending.
        :type account: str
        :param delegate: Address of the account allowed to spend.
        :type delegate: str
        :param amount: The amount to add.
        :type amount
        :return: The new allowance of the delegate on behalf of the account.
        :rtype: int
        """
        assert_positive_amount(amount)
        new_allowance = self.get_one(account, delegate) + amount
        self.set(account, delegate, new_allowance)
        return new_allowance

    def update(self, account, delegate, amount):
        """Increase or decrease an allowance, depending on the sign of amount.

        :param account: Address of the account allowing spending.
        :type account: str
        :param delegate: Address of the account allowed to spend.
        :type delegate: str
        :param amount: The amount to add or remove.
        :type amount
        :return: The new allowance of the delegate on behalf of the account.
        :rtype: int
        """
        op = self.increase if amount >= 0 else self.decrease
        return op(account, delegate, abs(amount))

    def set(self, account, delegate, amount):
        """Define an allowance to a specified amount.

        :param account: Address of the account allowing spending.
        :type account: str
        :param delegate: Address of the account allowed to spend.
        :type delegate: str
        :param amount: The amount to add or remove.
        :type amount
        :return: The new allowance of the delegate on behalf of the account.
        :rtype: int
        """
        assert_positive_amount(amount)
        self.get_all(account)[delegate] = amount

    def clear_one(self, account, delegate):
        """Delete allowance of delegate on account.

        :param account: Address of the account allowing spending.
        :type account: str
        :param delegate: Address of the account allowed to spend.
        :type delegate: str
        """
        del self.allowances[account][delegate]

    def clear_all(self, account):
        """Delete all allowances of specified account.

        :param account: Address of the account allowing spending.
        :type account: str
        """
        del self.allowances[account]

    def transaction(self, account, delegate, amount):
        """Creates a Context Manager wrapping the need of an allowance.
        If no exception is raised inside within the context, the amount will
        be removed from the delegate allowance.

        Usage:
        with allowances.transaction(from_address, sender, amount):
            # do something
        """
        this = self

        class _Context(object):

            def __enter__(self):
                this.require(account, delegate, amount)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if not exc_type:
                    this.decrease(account, delegate, amount)

        return _Context()


def transfer(balance_of, sender, to_address, amount):
    """Default transfer. Amount is taken out of sender account and put
    in provided address account, provided the sender has enough assets.

    :param balance_of: The mapping storing the balances of each customer.
    :type balance_of: dict[str,int]
    :param sender: Address of the transfer sender.
    :type sender: str
    :param to_address: Address of the transfer recipient.
    :type to_address: str
    :param amount: The amount transferred.
    :type amount: int
    :return: True if the operation was successful. False otherwise.
    :rtype: bool
    """
    balances = Balances(balance_of)
    balances.withdraw(sender, amount)
    balances.deposit(to_address, amount)
    events.transfer(sender, to_address, amount)
    return True


def mint(balance_of, total_supply, account, amount):
    """Default mint. Tokens are created and put into account.

    No other check is performed.

    :param balance_of: The mapping storing the balances of each customer.
    :type balance_of: dict[str,int]
    :param total_supply: The total supply of tokens before mint operation.
    :type total_supply: int
    :param account: Address of the sender who creates and receives the amount.
    :type account: str
    :type amount: int
    :param amount: The amount minted.
    :return: The new total supply.
    :rtype: int
    """
    new_balance = Balances(balance_of).deposit(account, amount)
    events.mint(account, amount, new_balance, total_supply)
    return total_supply + amount


def burn(balance_of, total_supply, account, amount):
    """Default burn. Tokens are destroyed, removed from an account.

    Sender must have sufficient funds.

    :param balance_of: The mapping storing the balances of each customer.
    :type balance_of: dict[str,int]
    :param total_supply: The total supply of tokens before burn operation.
    :type total_supply: int
    :param account: Account which destroys and loses the amount.
    :type account: str
    :param amount: The amount burnt.
    :type amount: int
    :return: The new total supply.
    :rtype: int
    """
    new_balance = Balances(balance_of).withdraw(account, amount)
    events.burn(account, amount, new_balance, total_supply)
    return total_supply - amount


def approve(allowances, account, delegate, amount):
    """Default approve. The specified address is allowed to spend
    specified amount on behalf of the sender.

    If another allowance existed for that address, it is replaced.

    :param allowances: The mapping storing the allowances of each customer.
    :type allowances: dict[str,dict[str,int]]
    :param account: Address of the account who approves an allowance on his
        behalf.
    :type account: str
    :param delegate: The address which will be allowed to spend tokens on
        behalf of the account's owner.
    :type delegate: str
    :param amount: The new allowance.
    :type amount: int
    :return: True if the operation was successful. False otherwise.
    :rtype: bool
    """
    Allowances(allowances).set(account, delegate, amount)
    return True


def update_approve(allowances, account, delegate, delta_amount):
    """Default update_approve. The specified address is allowed to spend
    an additional specified amount on behalf of the sender.

    That means existing allowances are preserved.

    :param allowances: The mapping storing the allowances of each customer.
    :type allowances: dict[str,dict[str,int]]

    :param account: Address of the account who approves an allowance on his
        behalf.
    :type account: str
    :param delegate: The address which will be allowed to spend tokens on
        behalf of the account's owner.
    :type delegate: str
    :param delta_amount: The top up amount of allowance. It can be negative.
    :type delta_amount: int
    :return: The new allowance of the approved address.
    :rtype: int
    """
    return Allowances(allowances).update(account, delegate, delta_amount)


def transfer_from(balance_of, allowances, delegate, from_address, to_address,
                  amount):
    """Default transfer_from. The amount is taken out of from address instead
    of delegate, provided delegate has sufficient allowance on from address.

    :param balance_of: The mapping storing the balances of each customer.
    :type balance_of: dict[str,int]
    :param allowances: The mapping storing the allowances of each customer.
    :type allowances: dict[str,dict[str,int]]
    :param delegate: Address of the delegate asking for a transfer on behalf of
        from_address.
    :type delegate: str
    :param from_address: Address of the transfer sender.
    :type from_address: str
    :param to_address: Address of the transfer recipient.
    :type to_address: str
    :param amount: The amount transferred.
    :type amount: int
    :return: True if the operation was successful. False otherwise.
    :rtype: bool
    """
    with Allowances(allowances).transaction(from_address, delegate, amount):
        return transfer(balance_of, from_address, to_address, amount)


def burn_from(balance_of, allowance, total_supply, delegate, from_address,
              amount):
    """Default burn_from. The amount is taken out of from address instead of
    sender, provided sender has sufficient allowance on from address.

    The amount is then destroyed.

    :param balance_of: The mapping storing the balances of each customer.
    :type balance_of: dict[str,int]
    :param allowance: The mapping storing the allowances of each customer.
    :type allowance: dict[str,dict[str,int]]
    :param total_supply: The total supply of tokens before burn operation.
    :type total_supply: int
    :param delegate: Address of the burn invoker.
    :type delegate: str
    :param from_address: Address of the account burning tokens.
    :type from_address: str
    :param amount: The amount transferred.
    :type amount: int
    :return: The new total supply.
    :rtype: int
    """
    with Allowances(allowance).transaction(from_address, delegate, amount):
        return burn(balance_of, total_supply, from_address, amount)
