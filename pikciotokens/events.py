import json
from datetime import datetime

_registered_events = set()
"""Names of all registered events. Pretty but unreliable."""
_registered_events_ids = set()
"""Ids of all registered events. Reliable."""


def registered_events():
    """Obtains the names of all registered events. This function is only
    trustworthy if each event was never replace by another one.

    To ensure an event is still valid, use is_registered.

    :return: A set of all registered events names.
    :rtype: set
    """
    return _registered_events.copy()


def is_registered(event):
    """Indicates if provided event is currently registered.

    :param: The event to check.
    :type: callable
    :return: True if the event exists. False otherwise.
    :rtype: bool
    """
    return id(event) in _registered_events_ids


def register(event_name, *args):
    """Creates and return an event of specified name accepting
    provided named parameters.

    When calling the event, parameters have to be provided by name only.
    Also, once registered, the event can be called from this modules directly,
    like:
        import events
        events.register("transfer", "sender", "recipient", "amount")
        events.transfer(sender="a", recipient="b", amount:18.3)

    :param event_name: The name of the event to create. If it exists already,
        it will be replaced.
    :type event_name: str
    :param args: The name of the arguments accepted by the event.
    :return: The created event.
    :rtype: callable
    """
    args = set(args)
    event_id = []  # Use an array to capture event id in closure.

    def _event(**kwargs):
        # event has to be still registered
        if event_id[0] not in _registered_events_ids:
            raise LookupError(
                "{} has already been unregistered.".format(event_name)
            )

        # args have to match event definition.
        if set(kwargs.keys()) != args:
            raise ValueError(
                'Event args ({}) do not match event definition ({}) of '
                'event {}'.format(
                    ', '.join(sorted(kwargs.keys())),
                    ', '.join(sorted(args)),
                    event_name
                )
            )
        # Print some JSON out. It will be captured by the executing context.
        print('{{"ts": "{asctime}", "event": "{event}", {msg}}}'.format(
            asctime=datetime.utcnow().isoformat(),
            event=event_name,
            msg=json.dumps(kwargs)
        ))

    # If an event with same name exists already, unregister it.
    if event_name in _registered_events:
        unregister(event_name)

    # Add the event to this module root and update registers.
    event_id[0] = id(_event)
    globals().update({event_name: _event})
    _registered_events.add(event_name)
    _registered_events_ids.add(event_id[0])
    return _event


def unregister(event):
    """Removes an event from the registrar. Its entry is deleted and it cannot
    be called anymore via the module or any reference.

    An attempt to unregister a missing event will do nothing.

    :param event: The event itself or its name.
    :type event: callable|str
    """
    event_name = event if isinstance(event, str) else event.__name__
    if event_name not in globals():
        return

    event = globals()[event_name]
    _registered_events_ids.remove(id(event))
    _registered_events.remove(event)
    del globals()[event_name]
