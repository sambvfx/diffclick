#!/usr/bin/env python
import sys
import platform
import time
import math
import operator
import threading

import pymouse


class Listen(pymouse.PyMouseEvent):
    """
    Mouse event lister.

    Start the service by calling `run`.
    """
    # leftclick = 1, middleclick = 2, rightclick = 3
    # default button if no button is specified
    DEFAULT_BUTTON = 9

    def __init__(self, button=None, *args, **kwargs):
        """
        Parameters
        ----------
        button : int
            Button to start / stop the ``Compare``
        """
        super(Listen, self).__init__(*args, **kwargs)

        if button is None:
            self.button = self.DEFAULT_BUTTON

        self.compare = Compare(self.callback)
        self.press = None
        self.mouse = pymouse.PyMouse()

    def click(self, x, y, button, press):
        if button == self.button:
            if press is True:
                self.press = True
                self.compare.start()
            elif press is False:
                self.press = False
                self.compare.stop()

    def callback(self):
        print '\n    | CLICK{0}'.format(self.mouse.position())
        self.mouse.press(*self.mouse.position())
        while self.press:
            pass
        self.mouse.release(*self.mouse.position())


class Compare(object):

    def __init__(self, callback, tolerance=1.8, start_delay=0,
                 callback_delay=0.01, refresh=0.008, size=(20, 20)):
        """
        Monitor an area under your mouse and click when the image buffers
        frames differ over a given tolerance.

        Parameters
        ----------
        callback : callable
            Function to call once a difference is detected.
        tolerance : float
            Trigger `callback` if the difference between the two frame
            histograms is larger than this value.
        start_delay : float
            Time to delay starting monitoring after `start` is called.
        callback_delay : float
            Time to wait before calling `callback` after a difference is
            detected.
        refresh : float
            Time between each frame image buffer to check for differences.
        size : tuple[int]
            Size under the cursor to monitor.
        """
        # specify the screen grab method based on the os
        self.grab = getattr(
            self, '_grab_{0}'.format(platform.system().lower()))

        if not self.grab:
            raise ValueError('{0} is not a supported os system.'.format(
                platform.system().lower()))

        self.thread = None
        self.event = None

        self.callback = callback
        self.tolerance = tolerance
        self.start_delay = start_delay
        self.callback_delay = callback_delay
        self.refresh = refresh

        self.mouse = pymouse.PyMouse()

        self.size = size

    def _grab_linux(self):
        """
        Linux specific logic for generating an Image of an area under the
        cursor.

        Returns
        -------
        ``Image``
        """
        from PIL import Image
        import gtk.gdk

        w = gtk.gdk.get_default_root_window()
        m_x, m_y = self.mouse.position()
        x, y = self.size
        pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, x, y)

        pb = pb.get_from_drawable(
            w, w.get_colormap(),
            m_x - (x/2),
            m_y - (y/2),
            0,
            0,
            x,
            y
        )
        if pb is not None:
            return Image.frombytes('RGB', self.size, pb.get_pixels())

    @classmethod
    def diff(cls, f1, f2):
        """
        Detect the difference between two images.

        Parameters
        ----------
        f1 : ``Image``
            Image buffer.
        f2 : ``Image``
            Image buffer.

        Returns
        -------
        float
        """
        h1 = f1.histogram()
        h2 = f2.histogram()

        return math.sqrt(
            reduce(
                operator.add, map(lambda a, b: (a - b) ** 2, h1, h2)
            ) / len(h1))

    def _compare(self, callback, event):
        """
        Compare the area under the cursor until either the `event` changes
        state (button released) or a tolerance over our specified threshold
        has been reached.

        Parameters
        ----------
        callback : callable
        event : ``threading.Event``
        """
        time.sleep(self.start_delay)

        last = self.grab()

        print '\n++ START(tolerance={0})'.format(self.tolerance)
        while not event.is_set():
            new = self.grab()
            diff = self.diff(last, new)
            sys.stdout.write('    | {0}                   \r'.format(diff))
            sys.stdout.flush()
            if diff > self.tolerance:
                sys.stdout.write('    | {0}'.format(diff))
                sys.stdout.flush()
                time.sleep(self.callback_delay)
                callback()
                break
            last = new
            time.sleep(self.refresh)

        # include whitespace to overwrite whatever was in stdout previously
        print '-- STOP                                                    '

    def start(self):
        if self.thread:
            raise RuntimeError('Already running!')

        self.event = threading.Event()

        self.thread = threading.Thread(
            target=self._compare, args=(self.callback, self.event))
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.thread is None:
            raise RuntimeError('You must start before you can stop!')
        self.event.set()
        self.thread.join()
        self.thread = None
        self.event = None


if __name__ == '__main__':
    l = Listen()
    l.run()
