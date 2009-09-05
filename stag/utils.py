
def curry(_curried_func, *args, **kwargs):
      def _curried(*moreargs, **morekwargs):
          return _curried_func(*(args+moreargs), **dict(kwargs, **morekwargs))
      return _curried

def isiter_not_string(obj):
    return hasattr(obj, '__iter__') and not isinstance(obj, (str, unicode))


