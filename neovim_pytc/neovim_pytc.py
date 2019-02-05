# This file is part of the neovim-pytc-example. It is currently hosted at
# https://github.com/mvilim/neovim-pytc-example
#
# neovim-pytc-example is licensed under the MIT license. A copy of the license can be
# found in the root folder of the project.

from typing import Callable

import os
import shutil
import argparse
import logging

from threading import Thread, Condition
import errno
import signal

from neovim import attach, Nvim

import curses
from curses import wrapper

import pylibtermkey as ptk

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
# uncomment this to add logging
# logger.addHandler(logging.FileHandler('neovim_pytc.log'))


class EventHandler:
    def __init__(self, handle, init=None, deinit=None):
        self.handle = handle
        self.init = init
        self.deinit = deinit


class UIRender(Thread):
    def __init__(self, stop_callback: Callable, nvim: Nvim, scr):
        Thread.__init__(self)
        self.nvim = nvim
        self.scr = scr
        self.closed = Condition()
        self.stop_callback = stop_callback
        self.is_stopping = False
        self.cursor_x = None
        self.cursor_y = None
        self.handlers = {'grid_line': EventHandler(self.grid_line, self.cursor_init, self.cursor_deinit),
                         'hl_attr_define': EventHandler(self.hl_attr_define),
                         'grid_scroll': EventHandler(self.grid_scroll, self.cursor_init, self.cursor_deinit),
                         'grid_cursor_goto': EventHandler(self.grid_cursor_goto), 'flush': EventHandler(self.flush)}
        self.reversed_colors = set()

    def stop(self):
        logger.debug('Pre-stop render loop')
        self.closed.acquire()
        if not self.is_stopping:
            self.is_stopping = True
            logger.debug('Stopping render loop')
            self.nvim.stop_loop()
            self.closed.wait()
            logger.debug('Render loop stop sent')
        self.closed.release()

    def run(self):
        try:
            self.nvim.run_loop(self.request_callback, self.notification_callback)
        finally:
            self.closed.acquire()
            self.is_stopping = True
            self.closed.notify()
            self.closed.release()
            self.stop_callback()
            self.clean_up()
            logger.debug('Render loop finished')

    def clean_up(self):
        logger.debug('Cleaning up render loop')
        logger.debug('Cleaned up render loop')

    def request_callback(self, event_name, events):
        logger.debug((event_name, events))

    def cursor_init(self, event):
        self.cursor_y, self.cursor_x = self.scr.getyx()

    def grid_line(self, event):
        grid = event[0]
        if grid != 1:
            raise Exception('Multigrid not supported')
        row = event[1]
        col = event[2]
        cells = event[3]
        hl = None
        for i, cell in enumerate(cells):
            text = cell[0]
            repeat = 1
            # if repeat is greater than 1, we are guaranteed to send an hl_id
            # https://github.com/neovim/neovim/blob/master/src/nvim/api/ui.c#L483
            if len(cell) > 1:
                hl = cell[1]
            if len(cell) > 2:
                repeat = cell[2]
            text = text * repeat
            # ignore failures because of the bottom right cursor behavior -- we should make this checking more robust
            try:
                other_attr = 0
                if hl in self.reversed_colors:
                    other_attr |= curses.A_REVERSE
                self.scr.addstr(row, col, text, curses.color_pair(hl) | other_attr)
            except:
                pass
            col = col + len(text)

    def cursor_deinit(self, event):
        self.scr.move(self.cursor_y, self.cursor_x)

    def hl_attr_define(self, event):
        hl_id = event[0]
        # rgb_attr = inst[1]
        cterm_attr = event[2]
        # info = inst[3]
        fg = cterm_attr.get('foreground', -1)
        bg = cterm_attr.get('background', -1)
        curses.init_pair(hl_id, fg, bg)
        # nvim api docs state that boolean keys here are only sent if true
        if 'reverse' in cterm_attr:
            self.reversed_colors.add(hl_id)
        else:
            self.reversed_colors.discard(hl_id)

    def grid_scroll(self, event):
        grid = event[0]
        top = event[1]
        bot = event[2]
        left = event[3]
        right = event[4]
        rows = event[5]
        cols = event[6]
        if grid != 1:
            raise Exception('Multigrid not supported')
        if cols != 0:
            raise Exception('Column scrolling not expected')
        logger.debug('scroll grid:%s top:%s bot:%s left:%s right:%s rows:%s cols:%s', grid, top, bot, left, right, rows,
                     cols)

        bot = bot - 1
        if rows > 0:
            start = top
            stop = bot - rows + 1
            step = 1
        elif rows < 0:
            start = bot
            stop = top - rows - 1
            step = -1
        else:
            raise AssertionError('Rows should not equal 0')

        # this is very inefficient, but there doesn't appear to be a curses function for extracting whole lines incl.
        # attributes. another alternative would be to keep our own copy of the screen buffer
        for i in range(start, stop, step):
            for j in range(left, right):
                c = self.scr.inch(i + rows, j)
                try:
                    self.scr.addch(i, j, c)
                except:
                    pass

    def grid_cursor_goto(self, event):
        grid = event[0]
        if grid != 1:
            raise Exception('Multigrid not supported')
        row = event[1]
        column = event[2]
        self.scr.move(row, column)

    def flush(self, event):
        self.scr.refresh()

    def notification_callback(self, event_name, events):
        logger.debug((event_name, events))
        if event_name == 'redraw':
            for event in events:
                event_subtype = event[0]
                event_instances = event[1:]
                handler: EventHandler = self.handlers.get(event_subtype, None)
                if handler:
                    if handler.init:
                        handler.init(event)
                    for inst in event_instances:
                        handler.handle(inst)
                    if handler.deinit:
                        handler.deinit(event)
        else:
            logger.debug('Skipping event of type %s', event_name)


class UIInput(Thread):
    def __init__(self, stop_callback, nvim: Nvim):
        Thread.__init__(self)
        self.nvim = nvim
        self.tk = None
        self.stop_callback = stop_callback
        self.is_stopping = False

    def stop(self):
        logger.debug('Pre-stop input loop')
        if not self.is_stopping:
            logger.debug('Stopping input loop')
            self.is_stopping = True
            os.kill(os.getpid(), signal.SIGQUIT)
            # there is a race condition here -- we may not be blocked on waitkey when this signal is sent, but we
            # may become blocked after it is received (if we have already passed the boolean check)
        logger.debug('Input loop stop sent')

    def clean_up(self):
        logger.debug('Cleaning up input loop')
        if self.tk:
            self.tk.stop()
        logger.debug('Cleaned up input loop')

    def init_signal_handlers(self):
        # should move these into the input thread?
        def quit_handler(_signum, _frame):
            logger.debug('Quit handler caught')
            self.stop()

        signal.signal(signal.SIGQUIT, quit_handler)

        def resize_handler(_signum, _frame):
            e = ptk.get_errno()
            new_size = shutil.get_terminal_size()
            logger.debug('Resize-window signal caught [%s]', new_size)
            curses.resizeterm(new_size.lines, new_size.columns)
            self.nvim.async_call(self.nvim.ui_try_resize, new_size.columns, new_size.lines)
            ptk.set_errno(e)

        signal.signal(signal.SIGWINCH, resize_handler)

    def run(self):
        self.init_signal_handlers()
        self.tk = ptk.TermKey(flags={ptk.TermKeyFlag.EINTR})
        self.tk.set_canonflags({ptk.TermKeyCanon.DELBS})
        try:
            while True:
                r, k = self.tk.waitkey()
                if self.is_stopping:
                    break
                if r == ptk.TermKeyResult.KEY:
                    logger.debug(r)
                    # see https://github.com/neovim/neovim/blob/master/src/nvim/tui/input.c for these remappings
                    if k.type() is ptk.TermKeyType.UNICODE and k.code() == 60:
                        key = '<lt>'
                    elif k.type() is ptk.TermKeyType.KEYSYM and k.code() is ptk.TermKeySym.ESCAPE:
                        key = '<Esc>'
                    else:
                        key = self.tk.strfkey(k, ptk.TermKeyFormat.VIM)
                    logger.debug('Received key [%s] with type [%s], bytes [%s]', key, type(key),
                                 bytes(key, 'utf8').hex())
                    self.nvim.async_call(self.nvim.input, key)
                elif r == ptk.TermKeyResult.ERROR and ptk.get_errno() == errno.EINTR:
                    logger.debug('Interrupted')
                else:
                    logger.debug(r)
                    raise Exception('Unexpected input received')
        finally:
            self.is_stopping = True
            self.stop_callback()
            self.clean_up()


def curses_main(stdscr, filename):
    height, width = stdscr.getmaxyx()

    args = ['/bin/env', 'nvim', '--embed']
    if filename:
        args.append(filename)
    nvim: Nvim = attach('child', argv=args)

    stdscr.clear()
    curses.use_default_colors()
    curses.curs_set(1)

    threads = list()

    def stop():
        logger.debug('Running stop callback')
        for thread in threads:
            logger.debug('Stopping a thread')
            thread.stop()

    input_thread = UIInput(stop, nvim)
    render_thread = UIRender(stop, nvim, stdscr)

    threads.append(input_thread)
    threads.append(render_thread)

    render_thread.start()

    nvim.async_call(nvim.ui_attach, width, height, rgb=True, ext_linegrid=True)

    # the input loop must be run in the main input thread to receive signals (SIGQUIT and SIGWINCH)
    try:
        input_thread.run()
    finally:
        logger.debug('Main thread finished')
        nvim.close()


def run_cli():
    parser = argparse.ArgumentParser('neovim_pytc')
    parser.add_argument('filename', help='The file to be opened', type=str, nargs='?', default=None)
    args = parser.parse_args()
    run(args.filename)


def run(filename=None):
    wrapper(curses_main, filename)
    logger.debug('Neovim pytc application finished')


if __name__ == '__main__':
    run_cli()
