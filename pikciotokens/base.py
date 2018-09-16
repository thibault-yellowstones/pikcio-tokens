from . import events

MAX_TOKEN_DECIMALS = 8


def assert_positive_amount(amount):
    """Check provided amount is positive. Raise an Exception otherwise.

    :param amount: The amount transferred.
    :type amount: int
    """
    if amount < 0:
        raise ValueError("Negative amounts ({}) are forbidden.".format(amount))


class Balances(object):
    """Utility Wrapper for the account balances."""

    def __init__(self, balance_of, missing_means_zero=True):
        self.balance = balance_of
        self.missing_means_zero = missing_means_zero

    def _default_balance(self):
        """Gets the balance of a missing account."""
        return 0 if self.missing_means_zero else None

    def _post_withdrawal(self, address):
        if self.missing_means_zero and not self.balance[address]:
            self.clear(address)

    def assert_balance(self, address, amount):
        """Check balance of address against amount.

        Raise an Exception if balance is insufficient.
        :param address: Address of the checked account.
        :type address: str
        :param amount: The amount to check.
        :type amount: int
        """
        if self.balance.get(address, 0) < amount:
            raise ValueError(
                "Account {} has insufficient funds ({}<{}).".format(
                    address, self.balance.get(address, 0), amount
                ))

    def clear(self, address):
        del self.balance[address]

    def get(self, address):
        return self.balance.get(address, self._default_balance())

    def deposit(self, address, amount):
        """Increase balance of address of specified amount.

        A balance entry is created if required.

        :param address: Address of the allowed sender.
        :type address: str
        :param amount: The amount to add.
        :type amount: int
        :return: The new balance of the sender.
        :rtype: int
        """
        assert_positive_amount(amount)
        self.balance[address] = self.balance.get(address, 0) + amount
        return self.balance[address]

    def withdraw(self, address, amount):
        """Decrease balance of address of specified amount.

        The amount is removed from the balance and the balance entry is deleted
        if it falls to 0. No check is performed at this stage, so ensure the
        balance exists and is high enough.

        :param address: Address of the allowed sender.
        :type address: str
        :param amount: The amount to remove.
        :type amount: int
        :return: The new balance of the sender.
        :rtype: int
        """
        assert_positive_amount(amount)
        self.assert_balance(address, amount)
        self.balance[address] -= amount
        new_balance = self.balance[address]
        self._post_withdrawal(address)
        return new_balance


class Allowances(object):

    def __init__(self, allowances, missing_means_zero=True,
                 zero_allows_empty_transfer=False):
        self.allowances = allowances
        self.missing_means_zero = missing_means_zero
        self.zero_allows_empty_transfer = zero_allows_empty_transfer

    def _default_allowance(self):
        """Gets the balance of a missing account."""
        return 0 if self.missing_means_zero else None

    def _post_decrease(self, account, delegate):
        if self.missing_means_zero and not self.allowances[account][delegate]:
            self.clear_one(account, delegate)
            if not self.allowances[account]:
                del self.allowances[account]

    def get_all(self, account):
        return self.allowances.get(account, {})

    def get_one(self, address, delegate):
        return self.get_all(address).get(delegate, self._default_allowance())

    def assert_allowance(self, account, delegate, amount):
        """Check allowance of sender on behalf of from_address.

        Raise an Exception if allowance is insufficient.

        :param account: Address of the allowed sender.
        :type account: str
        :param delegate: Address of the spender account.
        :type delegate: str
        :param amount: The amount to check.
        :type amount: int
        """
        account_allowance = self.get_one(account, delegate)
        if any((
            account_allowance is None,
            account_allowance == 0 and not self.zero_allows_empty_transfer,
            account_allowance < amount
        )):
            raise ValueError("{} has not enough approval to spend {} on "
                             "behalf of {}".format(delegate, amount, account))

    def decrease(self, account, delegate, amount):
        """Decrease allowance of sender on behalf of from_address.

        The amount is removed from the allowance and the allowance entry is deleted
        if it falls to 0. No check is performed at this stage, so ensure the
        allowance exists and is high enough.

        :param delegate: Address of the allowed sender.
        :type delegate: str
        :param account: Address of the spender account.
        :type account: str
        :param amount: The amount to remove.
        :type amount: int
        """
        assert_positive_amount(amount)
        if amount >= self.get_one(account, delegate):
            self.set(account, delegate, 0)
        else:
            self.get_all(account)[delegate] -= amount
        self._post_decrease(account, delegate)
        return self.get_one(account, delegate) or 0

    def increase(self, account, delegate, amount):
        assert_positive_amount(amount)
        allowances = self.get_all(account)
        allowances[delegate] = allowances.get(delegate, 0) + amount
        return allowances[delegate]

    def update(self, account, delegate, amount):
        if amount >= 0:
            return self.increase(account, delegate, amount)
        else:
            return self.decrease(account, delegate, -amount)

    def set(self, account, delegate, amount):
        assert_positive_amount(amount)
        self.get_all(account)[delegate] = amount

    def clear_one(self, address, delegate):
        del self.allowances[address][delegate]

    def clear_all(self, address):
        del self.allowances[address]


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


def mint(balance_of, total_supply, sender, amount):
    """Default mint. Tokens are created and put into sender's account.

    No other check is performed.

    :param balance_of: The mapping storing the balances of each customer.
    :type balance_of: dict[str,int]
    :param total_supply: The total supply of tokens before mint operation.
    :type total_supply: int
    :param sender: Address of the sender who creates and receives the amount.
    :type sender: str
    :type amount: int
    :param amount: The amount minted.
    :return: The new total supply.
    :rtype: int
    """
    new_balance = Balances(balance_of).deposit(sender, amount)
    events.mint(sender, amount, new_balance, total_supply)
    return total_supply + amount


def burn(balance_of, total_supply, sender, amount):
    """Default burn. Tokens are destroyed, removed from sender's account.

    Sender must have sufficient funds.

    :param balance_of: The mapping storing the balances of each customer.
    :type balance_of: dict[str,int]
    :param total_supply: The total supply of tokens before burn operation.
    :type total_supply: int
    :param sender: Address of the sender who destroys and loses the amount.
    :type sender: str
    :param amount: The amount burnt.
    :type amount: int
    :return: The new total supply.
    :rtype: int
    """
    new_balance = Balances(balance_of).withdraw(sender, amount)
    events.burn(sender, amount, new_balance, total_supply)
    return total_supply - amount


def approve(allowance, sender, to_address, amount):
    """Default approve. The specified address is allowed to spend
    specified amount on behalf of the sender.

    If another allowance existed for that address, it is replaced.

    :param allowance: The mapping storing the allowances of each customer.
    :type allowance: dict[str,dict[str,int]]
    :param sender: Address of the sender who approves an allowance on his
        behalf.
    :type sender: str
    :param to_address: The address which will be allowed to spend tokens on
        behalf of the sender.
    :type to_address: str
    :param amount: The new allowance.
    :type amount: int
    :return: True if the operation was successful. False otherwise.
    :rtype: bool
    """
    Allowances(allowance).set(sender, to_address, amount)
    return True


def add_approve(allowance, sender, to_address, delta_amount):
    """Default add_approve. The specified address is allowed to spend
    an additional specified amount on behalf of the sender.

    That means existing allowances are preserved.

    :param allowance: The mapping storing the allowances of each customer.
    :type allowance: dict[str,dict[str,int]]
    :param sender: Address of the sender who approves an allowance on his
        behalf.
    :type sender: str
    :param to_address: The address which will be allowed to spend tokens on
        behalf of the sender.
    :type to_address: str
    :param delta_amount: The top up amount of allowance. It can be negative.
    :type delta_amount: int
    :return: The new allowance of the approved address.
    :rtype: int
    """
    return Allowances(allowance).update(sender, to_address, delta_amount)


def transfer_from(balance_of, allowance, sender, from_address, to_address,
                  amount):
    """Default transfer_from. The amount is taken out of from address instead
    of sender, provided sender has sufficient allowance on from address.

    :param balance_of: The mapping storing the balances of each customer.
    :type balance_of: dict[str,int]
    :param allowance: The mapping storing the allowances of each customer.
    :type allowance: dict[str,dict[str,int]]
    :param sender: Address of the transfer sender.
    :type sender: str
    :param from_address: Address of the transfer sender.
    :type from_address: str
    :param to_address: Address of the transfer recipient.
    :type to_address: str
    :param amount: The amount transferred.
    :type amount: int
    :return: True if the operation was successful. False otherwise.
    :rtype: bool
    """
    allowances = Allowances(allowance)
    allowances.assert_allowance(sender, from_address, amount)

    # Check the transfer operation worked.
    if not transfer(balance_of, from_address, to_address, amount):
        return False

    allowances.decrease(sender, from_address, amount)
    return True


def burn_from(balance_of, allowance, total_supply, sender, from_address,
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
    :param sender: Address of the burn invoker.
    :type sender: str
    :param from_address: Address of the account burning tokens.
    :type from_address: str
    :param amount: The amount transferred.
    :type amount: int
    :return: The new total supply.
    :rtype: int
    """
    allowances = Allowances(allowance)
    allowances.assert_allowance(sender, from_address, amount)

    new_supply = burn(balance_of, total_supply, from_address, amount)
    # Check the burn operation worked.
    if new_supply == total_supply:
        return new_supply

    allowances.decrease(sender, from_address, amount)
    return new_supply
