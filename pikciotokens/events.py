import logging
import types

__EVENTS_MIN_LEVEL = 100

__next_level = __EVENTS_MIN_LEVEL


def init():
    logging.basicConfig(
        format='{"datestamp": "%(asctime)s", "event": "%(levelname)s", "args": "%(message)s"}',
        level=__EVENTS_MIN_LEVEL
    )


def register(event_name, *args):
    def event():
        logging.log(event_name, '')
    event_code = types.CodeType(args,
                                event.func_code.co_nlocals,
                                event.func_code.co_stacksize,
                                event.func_code.co_flags,
                                event.func_code.co_code,
                                event.func_code.co_consts,
                                event.func_code.co_names,
                                event.func_code.co_varnames,
                                event.func_code.co_filename,
                                event_name,
                                event.func_code.co_firstlineno,
                                event.func_code.co_lnotab)

    return types.FunctionType(event_code, event.func_globals, event_name)

    logging.addLevelName(__next_level, event_name)
    globals().update(event_name, )


def transfer(from_address, to_address, amount):
    logging.log("event")
