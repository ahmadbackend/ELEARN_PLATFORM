from django.http import HttpResponseForbidden
from functools import wraps

def user_type_required(user_type):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):  
            user = request.user
            if hasattr(user, 'user_cat') and user.user_cat == user_type:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("You are not authorized to access this page.")
        return _wrapped_view
    return decorator

