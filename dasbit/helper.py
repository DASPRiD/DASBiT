import datetime

def timesince(date, suffix=' ago'):
    chunks = (
        (60 * 60 * 24 * 365, lambda n: 'year' if n is 1 else 'years'),
        (60 * 60 * 24 * 30, lambda n: 'month' if n is 1 else 'months'),
        (60 * 60 * 24 * 7, lambda n: 'week' if n is 1 else 'weeks'),
        (60 * 60 * 24, lambda n: 'day' if n is 1 else 'days'),
        (60 * 60, lambda n: 'hour' if n is 1 else 'hours'),
        (60, lambda n: 'minute' if n is 1 else 'minutes')
    )

    now   = datetime.datetime.utcnow()
    delta = now - date
    since = delta.days * 24 * 60 * 60 + delta.seconds

    if since <= 0:
        return '0 minutes' + suffix

    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds

        if count != 0:
            break

    s = '%d %s' % (count, name(count))

    if i + 1 < len(chunks):
        seconds2, name2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2

        if count2 != 0:
            s += ' and %d %s' % (count2, name2(count2))

    s += suffix

    return s
