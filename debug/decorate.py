import sys
import os

# make line profiler visible from inside blender
sys.path.append('/home/david/.local/lib/python3.7/site-packages')
import line_profiler as lp


def uniquify(file):
    name, ext = os.path.splitext(file)
    count = 1

    while os.path.exists(file):
        file = name + str(count) + ext
        count += 1
    return file


def profile(func):
    mod = sys.modules[func.__module__]
    file = mod.__file__ + '.lprof'
    profilr = lp.LineProfiler()

    def wrap(*args, **kwargs):
        ret = profilr(func)(*args, **kwargs)

        stats = profilr.get_stats()
        with open(uniquify(file + '.txt'), 'w') as s:
            lp.show_text(stats.timings, stats.unit, stream=s)

        return ret
    return wrap

