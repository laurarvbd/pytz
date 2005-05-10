#!/usr/bin/env python
'''
$Id: tzinfo.py,v 1.9 2004/06/04 07:48:19 zenzen Exp $
'''

__rcs_id__  = '$Id: tzinfo.py,v 1.9 2004/06/04 07:48:19 zenzen Exp $'
__version__ = '$Revision: 1.9 $'[11:-2]

from datetime import datetime, timedelta, tzinfo
from bisect import bisect_right

_timedelta_cache = {}
def memorized_timedelta(seconds):
    '''Create only one instance of each distinct timedelta'''
    try:
        return _timedelta_cache[seconds]
    except KeyError:
        delta = timedelta(seconds=seconds)
        _timedelta_cache[seconds] = delta
        return delta

_datetime_cache = {}
def memorized_datetime(*args):
    '''Create only one instance of each distinct datetime'''
    try:
        return _datetime_cache[args]
    except KeyError:
        dt = datetime(*args)
        _datetime_cache[args] = dt
        return dt

_ttinfo_cache = {}
def memorized_ttinfo(*args):
    '''Create only one instance of each distinct tuple'''
    try:
        return _ttinfo_cache[args]
    except KeyError:
        ttinfo = (
                memorized_timedelta(args[0]),
                memorized_timedelta(args[1]),
                args[2]
                )
        _ttinfo_cache[args] = ttinfo
        return ttinfo

class BaseTzInfo(tzinfo):
    __slots__ = ()
    def __str__(self):
        return self._zone

_notime = memorized_timedelta(0)

class StaticTzInfo(BaseTzInfo):
    __slots__ = ()
    _utcoffset = None
    _tzname = None
    _zone = None

    def utcoffset(self,dt):
        return self._utcoffset

    def dst(self,dt):
        return _notime

    def tzname(self,dt):
        return self._tzname

    def __call__(self):
        return self # In case anyone thinks this is a Class and not an instance

    def __repr__(self):
        return '<StaticTzInfo %r>' % (self._zone,)

class DstTzInfo(BaseTzInfo):
    __slots__ = ()
    _utc_transition_times = None
    _transition_times = None
    _transition_info = None
    _zone = None

    _tzinfos = None
    _my_transition_info = None
    _is_dst = False

    def __init__(self, _inf=None, _tzinfos=None):
        if _inf:
            self._tzinfos = _tzinfos
            self._utcoffset, self._dst, self._tzname = _inf
        else:
            _tzinfos = {}
            self._tzinfos = _tzinfos
            self._utcoffset, self._dst, self._tzname = self._transition_info[0]
            _tzinfos[self._transition_info[0]] = self
            for inf in self._transition_info[1:]:
                if not _tzinfos.has_key(inf):
                    _tzinfos[inf] = self.__class__(inf, _tzinfos)

    def fromutc(self, dt):
        dt = dt.replace(tzinfo=None)
        idx = max(0, bisect_right(self._utc_transition_times, dt) - 1)
        inf = self._transition_info[idx]
        return (dt + inf[0]).replace(tzinfo=self._tzinfos[inf])

    def utcoffset(self, dt):
        # Round to nearest minute or datetime.strftime will complain
        secs = self._utcoffset.seconds + self._utcoffset.days*86400
        return memorized_timedelta(seconds=int((secs+30)/60)*60)

    def dst(self, dt):
        # Round to nearest minute or datetime.strftime will complain
        return memorized_timedelta(seconds=int((self._dst.seconds+30)/60)*60)

    def tzname(self, dt):
        return self._tzname

    def __repr__(self):
        if self._utcoffset > _notime:
            return '<DstTzInfo %r %s+%s>' % (
                    self._zone, self._tzname, self._utcoffset
                )
        else:
            return '<DstTzInfo %r %s%s>' % (
                    self._zone, self._tzname, self._utcoffset
                )
