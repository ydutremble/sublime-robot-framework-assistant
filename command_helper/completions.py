import re
from json import load as json_load
try:
    from current_view import KW_COMPLETION
    from current_view import VARIABLE
except:
    from .current_view import KW_COMPLETION
    from .current_view import VARIABLE

VAR_RE_STRING = '[\$\@\&]\{?\w*$'


class VarMode(object):
    """Which contents mode is used for variables

    Describes how variable is found from the Sublime prefix
    """
    no_brackets = 1
    two_brackets = 2
    start_bracket = 3


def get_completion_list(view_index, prefix):
    if re.search(VAR_RE_STRING, prefix):
        return get_var_completion_list(view_index, prefix)
    else:
        return get_kw_completion_list(view_index, prefix)


def get_kw_re_string(prefix):
    prefix = str(prefix)
    re_string = '(?i)('
    qualifier = '.*'
    for index in prefix:
        re_string = '{re_string}{qualifier}{index}'.format(
            re_string=re_string, qualifier=qualifier, index=index)
    re_string = '{re_string}{close_re}'.format(
        re_string=re_string, close_re=')')
    return re_string


def get_kw_completion_list(view_index, prefix):
    pattern = re.compile(get_kw_re_string(prefix))
    match_keywords = []
    for keyword in get_keywords(view_index):
        kw = keyword[0]
        lib = keyword[1]
        if pattern.search(kw):
            match_keywords.append(create_kw_completion_item(kw, lib))
    return match_keywords


def get_var_re_string(prefix):
    prefix = str(prefix)
    ignore_case = '(?i)'
    if not re.search(VAR_RE_STRING, prefix):
        re_string = '{0}\\{1}'.format(ignore_case, prefix)
    else:
        re_string = ignore_case
        pattern = re.compile('[\$\@\&]')
        var_position = 0
        for index in prefix:
            if var_position == 0 and pattern.search(index):
                var_position = 1
            if var_position == 1:  # @ or $ & character
                re_string = '{0}\\{1}'.format(re_string, index)
                var_position = 2
            elif var_position == 2:  # { character
                re_string = '{0}\\{1}'.format(re_string, index)
                var_position = 3
            elif var_position == 3:  # rest of the variable
                re_string = '{0}.*{1}'.format(re_string, index)
    return re_string


def get_var_completion_list(view_index, prefix):
    pattern = re.compile(get_var_re_string(prefix))
    match_vars = []
    for var in get_variables(view_index):
        if pattern.search(var):
            match_vars.append(create_var_completion_item(
                var, VarMode.no_brackets))
    return match_vars


def create_kw_completion_item(kw, source):
    trigger = '{trigger}\t{hint}'.format(trigger=kw, hint=source)
    return (trigger, kw.replace('_', ' ').title())


def create_var_completion_item(var, mode):
    if mode == VarMode.no_brackets:
        return (var, '{0}'.format(var[1:]))
    elif mode == VarMode.two_brackets:
        return (var, '{0}'.format(var[2:-1]))
    elif mode == VarMode.start_bracket:
        return (var, '{0}'.format(var[2:]))


def _get_data(view_index):
    with open(view_index) as f:
        return json_load(f)


def get_keywords(view_index):
    return _get_data(view_index)[KW_COMPLETION]


def get_variables(view_index):
    return _get_data(view_index)[VARIABLE]
