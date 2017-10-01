#!/usr/bin/env python
# coding: utf-8

"""
This module exports a single function which allows the user to call
a function periodically with high precision and absolute timing.
"""

__all__ = ['periodicx']
__version__ = '1.0'
__author__ = 'Michael Cipold'
__email__ = 'github@cipold.de'
__license__ = 'MPL-2.0'

import sched
import signal
import time
from threading import Thread, Event


class PeriodicExecutor:
	"""
	Helper class to execute a function periodically with high precision and absolute timing.
	"""
	_next_time = 0
	_next_event = None
	_cancelled = False
	_thread = None
	_sleep_event = Event()

	def __init__(self, func, period, *args, handle_sigint=True, skip_missed=True, **kwargs):
		"""
		Prepare execution
		:param func: function to be executed periodically
		:param period: amount of time between two starts of runs
		:param args: arguments passed to the function
		:param handle_sigint: can be set to false if handling of SIGINT is not desired
		:param skip_missed: do not try to catch up missed runs but continue with the next one
		:param kwargs: arguments passed to the function
		"""
		self.func = func
		self.period = period
		self.args = args
		self.skip_missed = skip_missed
		self.kwargs = kwargs

		self._scheduler = sched.scheduler(time.time, self._sleep)

		# Wire up signal to gracefully stop blocking, endless run
		if handle_sigint:
			signal.signal(signal.SIGINT, self._signal_handler)

	def run(self, delay=None, blocking=True):
		"""
		Main function executing the periodic run of a given function using scheduled events.
		:param delay: time which should be waited before first run
		:param blocking: run scheduler blocking or in a separate thread
		"""
		self._cancelled = False

		if delay is None:
			# Execute first run immediately
			self._next_time = time.time()
			self._single()
		else:
			# Schedule first run
			self._next_time = time.time() + delay
			self._next_event = self._scheduler.enterabs(self._next_time, 1, self._single)

		if blocking:
			# Execute scheduler (blocking)
			self._scheduler.run()
		else:
			self._thread = Thread(target=self._scheduler.run)
			self._thread.start()

	def cancel(self):
		self._cancelled = True

		if self._next_event is not None:
			try:
				self._scheduler.cancel(self._next_event)
			except ValueError:
				# Ignore
				pass

		self._sleep_event.set()

		if self._thread is not None:
			self._thread.join()

	def _single(self):
		"""
		Single execution of a given function automatically scheduling the next event.
		"""
		if self._cancelled:
			return

		# Execute function
		self.func(*self.args, **self.kwargs)

		# Determine time for next run
		self._next_time += self.period

		if self.skip_missed:
			# Skip all missed executions
			while self._next_time < time.time():
				self._next_time += self.period

		# Schedule next run
		self._next_event = self._scheduler.enterabs(self._next_time, 1, self._single)

	def _sleep(self, seconds):
		"""
		Interruptible sleep function
		:param seconds: time to sleep
		"""
		self._sleep_event.clear()
		self._sleep_event.wait(timeout=seconds)

	def _signal_handler(self, signum, _frame):
		"""
		Cancel scheduled event and stop execution
		:param signum: signal number
		:param _frame: unused parameter current stack frame
		"""
		if signum == signal.SIGINT:
			self.cancel()


def periodicx(func, period, *args, delay=None, blocking=True, handle_sigint=True, skip_missed=True, **kwargs):
	"""
	Execute a function periodically with high precision and absolute timing.
	:param func: function to be executed periodically
	:param period: amount of time between two starts of runs
	:param args: arguments passed to the function
	:param delay: time which should be waited before first run
	:param blocking: execute this function blocking
	:param handle_sigint: can be set to false if handling of SIGINT is not desired
	:param skip_missed: do not try to catch up missed runs but continue with the next one
	:param kwargs: arguments passed to the function
	:returns executor on non-blocking run which can be used to cancel
	"""
	executor = PeriodicExecutor(func, period, *args, handle_sigint=handle_sigint, skip_missed=skip_missed, **kwargs)
	executor.run(delay=delay, blocking=blocking)
	if not blocking:
		return executor
