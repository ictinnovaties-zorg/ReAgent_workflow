'''
Implements a variant of `call` and `check_call` from the subprocess package that logs the output of the call. The extra side-effect is that apart from running the call, they also pipe the output to the root logger. 
'''

import subprocess
import select
from logging import DEBUG, ERROR, INFO, getLogger

def logged_check_call(*args, **kwargs):
    """
    Run the call, but also log any output to the root logger. Mimics the behavior of check_call, i.e. try and run the code and returning CalledProcessError if it does not work. 

    Note that this acts as a wrapper around `logged_call` and simply passes any of the arguments and keyword arguments on to that function. 
    """
    return_val = logged_call(*args, **kwargs)
    if return_val != 0:
        raise subprocess.CalledProcessError(return_val, *args)

def logged_call(popenargs, logger=getLogger(''), stdout_log_level=INFO, stderr_log_level=ERROR, **kwargs):
    """
    Variant of subprocess.call ([adapted from here](https://gist.github.com/bgreenlee/1402841)) that accepts a logger instead of stdout/stderr,
    and logs stdout messages via logger.debug and stderr messages via
    logger.error.

    Args:
        popenargs (list): list of strings that together make up the command. See `subprocess.call` for more details.
        logger (logger): a logger to pass the output of the command to, this defaults to the root logger (`logging.getLogger('')`).
        stdout_log_level (int): the log level used for stdout. See the logging module for more details.
        stderr_log_level (int): the log level used for stderr. See the logging module for more details.

    Note that the remaing keyword arguments (`**kwargs`) will be passed on to `Popen`.

    TODO:

    - Remove b'' before the captured logging output
    """
    child = subprocess.Popen(popenargs, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, **kwargs)

    log_level = {child.stdout: stdout_log_level,
                 child.stderr: stderr_log_level}

    def check_io():
        ready_to_read = select.select([child.stdout, child.stderr], [], [], 1000)[0]
        for io in ready_to_read:
            line = io.readline()
            logger.log(log_level[io], line[:-1])

    # keep checking stdout/stderr until the child exits
    while child.poll() is None:
        check_io()

    check_io()  # check again to catch anything after the process exits

    return child.wait()
