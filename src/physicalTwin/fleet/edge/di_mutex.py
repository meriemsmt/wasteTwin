# https://www.dexterindustries.com
#
# Copyright (c) 2019 Dexter Industries
# Released under the MIT license (http://choosealicense.com/licenses/mit/).
# For more information see https://github.com/DexterInd/DI_Sensors/blob/master/LICENSE.md
#
# Python mutex

from __future__ import print_function
from __future__ import division

import time
import fcntl
import os
import atexit


class DI_Mutex(object):
    """ Dexter Industries mutex """

    def __init__(self, name, loop_time = 0.0001):
        """ Initialize """

        self.Filename = "/run/lock/DI_Mutex_" + name
        self.LoopTime = loop_time
        self.Handle = None

        try:
            open(self.Filename, 'w')
            if os.path.isfile(self.Filename):
                os.chmod(self.Filename, 0o777)
        except Exception as e:
            pass

        # Register the exit method
        atexit.register(self.__exit_cleanup__) # register the exit method

    def __exit_cleanup__(self):
        """ Called at exit to clean up """

        self.release()

    def acquire(self):
        """ Acquire the mutex """

        while True:
            try:
                self.Handle = open(self.Filename, 'w')
                # lock
                fcntl.lockf(self.Handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except IOError: # already locked by a different process
                time.sleep(self.LoopTime)
            except Exception as e:
                print(e)

    def release(self):
        """ Release the mutex """

        if self.Handle is not None and self.Handle is not True:
            self.Handle.close()
            self.Handle = None
            time.sleep(self.LoopTime)
