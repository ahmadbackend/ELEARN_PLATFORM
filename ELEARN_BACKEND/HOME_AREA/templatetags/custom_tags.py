from django import template

register = template.Library()

@register.filter

def get_dashboard_url(user_type):
    user_type = user_type.lower()
    if user_type == 'student':
        return 'STUDENTS:Dashboard'
    elif user_type == 'instructor':
        return 'instructor:Dashboard'
    return '' 

