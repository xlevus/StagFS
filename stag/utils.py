#    Copyright (C) 2009  Chris Targett  <chris@xlevus.net>
#
#    This file is part of StagFS.
#
#    StagFS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    StagFS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with StagFS.  If not, see <http://www.gnu.org/licenses/>.
#

def curry(_curried_func, *args, **kwargs):
      def _curried(*moreargs, **morekwargs):
          return _curried_func(*(args+moreargs), **dict(kwargs, **morekwargs))
      return _curried

def isiter_not_string(obj):
    return hasattr(obj, '__iter__') and not isinstance(obj, (str, unicode))


