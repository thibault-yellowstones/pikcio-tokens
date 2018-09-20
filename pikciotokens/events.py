import json
import logging

LOG_MIN_LEVEL = 100
LOGGER_NAME = 'pikcio-events'

_registered_events = set()
"""Names of all registered events. Pretty but unreliable."""
_registered_events_ids = set()
"""Ids of all registered events. Reliable."""
_log_level_index = LOG_MIN_LEVEL


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

    :param: The event to check or its name.
    :type: callable|str
    :return: True if the event exists. False otherwise.
    :rtype: bool
    """
    if isinstance(event, str):
        event = globals().get(event, None)
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

    Events are dispatched using the standard logging module. To subscribe to an
    an event notification, add an appropriate handler to the events logger.

    :param event_name: The name of the event to create. If it exists already,
        it will be replaced.
    :type event_name: str
    :param args: The name of the arguments accepted by the event.
    :return: The created event.
    :rtype: callable
    """
    global _log_level_index

    args = set(args)
    event_id = []  # Use an array to capture event id in closure.
    level = _log_level_index
    logger = logging.getLogger(LOGGER_NAME)

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
                '{} test'.format(
                    ', '.join(sorted(kwargs.keys())),
                    ', '.join(sorted(args)),
                    event_name
                )
            )
        # This log can be caught be any handler to process it.
        logger.log(level, msg=json.dumps(kwargs).strip('{}'))

    # Now that event is defined, fetch its unique id.
    event_id.append(id(_event))

    # If an event with same name exists already, unregister it.
    if event_name in _registered_events:
        unregister(event_name)

    # Bind event name to a log level.
    logging.addLevelName(level, event_name)
    _log_level_index += 1

    # Add the event to this module root and update registers.
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
