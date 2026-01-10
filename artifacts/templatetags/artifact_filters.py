from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Dict lookup filter for templates"""
    return dictionary.get(key)


@register.filter
def get_badge_color(color_class):
    """Convert product color class to badge color classes"""
    color_map = {
        'bg-green-500': 'bg-green-100 text-green-700',
        'bg-red-500': 'bg-red-100 text-red-700',
        'bg-blue-500': 'bg-blue-100 text-blue-700',
        'bg-indigo-500': 'bg-indigo-100 text-indigo-700',
        'bg-orange-500': 'bg-orange-100 text-orange-700',
        'bg-yellow-500': 'bg-yellow-100 text-yellow-700',
        'bg-purple-500': 'bg-purple-100 text-purple-700',
        'bg-pink-500': 'bg-pink-100 text-pink-700',
        'bg-teal-500': 'bg-teal-100 text-teal-700',
        'bg-cyan-500': 'bg-cyan-100 text-cyan-700',
    }
    return color_map.get(color_class, 'bg-emerald-100 text-emerald-700')
