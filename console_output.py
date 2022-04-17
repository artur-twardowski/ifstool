from sys import stdout

_last_line_is_status = False


def _ansi_cseq(*args):
    for s in args:
        stdout.write("\x1b[%s" % s)


def _reset_current_line():
    _ansi_cseq("0G", "0m", "0K")


def _format(formatspec, do_print=True):
    if do_print:
        _ansi_cseq(formatspec)
    else:
        return "\x1b[%s" % formatspec


def print_message(message, formatting=None):
    global _last_line_is_status
    if _last_line_is_status:
        _reset_current_line()
    if formatting is not None:
        _format(formatting)
    print(message)
    _last_line_is_status = False


def print_error(message):
    print_message(message, "1;31m")


def print_warning(message):
    print_message(message, "1;33m")


def print_debug(message):
    print_message(message, "0;35m")


def print_prompt(prompt, options, default_option):
    global _last_line_is_status
    if _last_line_is_status:
        _reset_current_line()

    stdout.write(prompt)
    opts_str = " ["
    for opt in options:
        hotkey_pos = opt.find('&') + 1
        hotkey = opt[hotkey_pos]
        highlight = ""
        if hotkey == default_option:
            highlight = _format("1;32m", False)
        else:
            highlight = _format("1m", False)
        highlight += hotkey + _format("0m", False)

        opt = opt.replace("&" + hotkey, highlight)
        opts_str += "%s/" % opt
    stdout.write(opts_str[:-1] + "] ")
    stdout.flush()


def print_status(status):
    global _last_line_is_status

    _reset_current_line()
    stdout.write(status)
    stdout.flush()
    _last_line_is_status = True


def create_progress_bar(position, maximum, width):
    BLK_CHARS = ['\u258f', '\u258e', '\u258d', '\u258c', 
                 '\u258b', '\u258a', '\u2589', '\u2588']

    substeps = len(BLK_CHARS)
    result = ""

    segments = int(position * width * substeps / maximum)
    while segments > 0:
        if segments > substeps:
            result += BLK_CHARS[-1]
            segments -= substeps
        else:
            result += BLK_CHARS[segments-1]
            segments = 0

    while len(result) < width:
        result += " "

    return "[%s]" % result

