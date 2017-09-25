# periodicx
This module exports a single function which allows the user to call a function periodically with high precision and absolute timing.

## Installation
Using `git clone`
```bash
git clone https://github.com/cipold/periodicx
cd periodicx
python setup.py install
```

## How to use
### Simple example
This example shows a simple test program printing "Hello, World!" once per second.
```python
from periodicx import periodicx


def print_hello():
	print("Hello, World!")


periodicx(print_hello, 1.0)
```

### Arguments
Keyword and positional parameters can be passed to the function as this example illustrates:
```python
from periodicx import periodicx


def print_hello(greeting, name):
	print("%s, %s!" % (greeting, name))


periodicx(print_hello, 1.0, "Welcome", name="Friend")
```

### Delay
Start periodic run after an initial delay.
```python
from periodicx import periodicx


def print_hello():
	print("Hello, World!")


periodicx(print_hello, 1.0, delay=3.0)
```

### Non-blocking execution
periodicx can be executed non-blocking.
```python
import time

from periodicx import periodicx


def print_hello():
	print("Hello, World!")


executor = periodicx(print_hello, 1.0, blocking=False)
time.sleep(5.0)
executor.cancel()
```

### Parameter change
Parameters can be changed when executed non-blocking:
```python
import time

from periodicx import periodicx


def print_hello(name):
	print("Hello, %s!" % name)


def print_welcome(name):
	print("Welcome, %s!" % name)


# prints Hello, World!
executor = periodicx(print_hello, 0.4, blocking=False, name="World")
time.sleep(1.0)

# prints Hello, Universe!
executor.kwargs = {"name": "Universe"}
time.sleep(1.0)

# prints Welcome, Universe!
executor.func = print_welcome
time.sleep(1.0)

executor.cancel()
```

## Details
### Handling missed executions
Sometimes the given function might not be called on time for various reasons (CPU usage, IO, ...). The parameter `skip_missed` specifies what should happen with the missed calls. By default regularity is preferred over completeness which means that all missed runs are skipped.

The following example illustrates the effect of changing the `skip_missed` parameter.
```python
import time

from periodicx import periodicx

last = None
first = None
count = 0
period = 0.001


def evaluate():
	global first, last, count

	now = time.time() * 1000

	if first is None:
		first = now
		last = now

	print("#%03d: abs. diff: %.1f ms\tdiff. since last run: %.1f ms" % (
		count, first + count * period * 1000 - now, now - last
	))
	count += 1
	last = now


executor = periodicx(evaluate, period, blocking=False, skip_missed=False)
time.sleep(1.0)
executor.cancel()
```
The example output shows the run number, the absolute time difference and the time difference since the last run.

This is how missed runs look like for `skip_missed=False`:
```
...
#645: abs. diff: -0.0 ms	diff. since last run: 1.0 ms
#646: abs. diff: -0.0 ms	diff. since last run: 1.0 ms
#647: abs. diff: -0.0 ms	diff. since last run: 1.0 ms
#648: abs. diff: -2.7 ms	diff. since last run: 3.7 ms
#649: abs. diff: -1.8 ms	diff. since last run: 0.1 ms
#650: abs. diff: -0.8 ms	diff. since last run: 0.0 ms
#651: abs. diff: -0.0 ms	diff. since last run: 0.2 ms
#652: abs. diff: -0.0 ms	diff. since last run: 1.0 ms
#653: abs. diff: -0.0 ms	diff. since last run: 1.0 ms
#654: abs. diff: -0.0 ms	diff. since last run: 1.0 ms
#655: abs. diff: -0.0 ms	diff. since last run: 1.0 ms
...
```
You can see that the missed runs are caught up very quickly and afterwards the function executes regularly again.

However if you set `skip_missed=True` the output after a missed run looks like this:
```
...
#176: abs. diff: -0.1 ms	diff. since last run: 1.0 ms
#177: abs. diff: -0.1 ms	diff. since last run: 1.0 ms
#178: abs. diff: -0.1 ms	diff. since last run: 1.0 ms
#179: abs. diff: -0.1 ms	diff. since last run: 1.0 ms
#180: abs. diff: -2.5 ms	diff. since last run: 3.4 ms
#181: abs. diff: -2.1 ms	diff. since last run: 0.6 ms
#182: abs. diff: -2.1 ms	diff. since last run: 1.0 ms
#183: abs. diff: -2.1 ms	diff. since last run: 1.0 ms
#184: abs. diff: -2.1 ms	diff. since last run: 1.0 ms
#185: abs. diff: -2.1 ms	diff. since last run: 1.0 ms
...
```
As you can see the regularity is restored immediately and no frames are caught up.

### Signal handling
By default the signal SIGINT is handled and causes cancelling the periodic run.

You can disable the handler by setting `handle_sigint=False`.