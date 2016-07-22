# diffclick
Automatically click the mouse after a change is detected under your cursor.

Usage
-----

terminal
```
$: diffclick/monitor.py
```

python
```python
>>> import diffclick.monitor
# run comparisons when right click is held
>>> m = diffclick.monitor.Listen(button=3)
>>> m.run()
```

After starting the listener, the `listener.button` (read: mouse button) will start the `Compare` operation when the button is pressed, and stop when it is released. If a change is detected while `Compare` is running, a *mouse1* click event will be issued and not be released until the `listener.button` is released.
