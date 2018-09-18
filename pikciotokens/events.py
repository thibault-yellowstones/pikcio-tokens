import json
from datetime import datetime

EVENT_FMT = '{{"ts": "{asctime}", "event": "{event}", {msg}}}'


def register(event_name, *args):
    args = set(args)

    def _event(**kwargs):
        if set(kwargs.keys()) != args:
            raise ValueError(
                'Event args ({}) do not match event definition ({}) of '
                'event {}'.format(
                    ', '.join(sorted(kwargs.keys())),
                    ', '.join(sorted(args)),
                    event_name
                )
            )
        print(EVENT_FMT.format(
            asctime=datetime.utcnow().isoformat(),
            event=event_name,
            msg=json.dumps(kwargs).lstrip('{').rstrip('}')
        ))

    globals().update({event_name: _event})
    return _event
