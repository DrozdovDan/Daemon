# DAEMON

Current daemon can be used to periodically execute several commands in the background of an Unix system.

## Installation

Use `git clone` to get your local version of the daemon.

## Usage

Before start this daemon make sure to install all requirements using `pip install -r requirements.txt`.

You can manage your own configs of daemon by changing the default settings:
```python
pidfile = os.getcwd() + "/conf/daemon-naprimer.pid"

commands = os.getcwd() + "/conf/commands.txt"

stdin = "/dev/null"

stdout = "/dev/null"

stderr = os.getcwd() + "/conf/stderr.err"

sleeptime = 10
```

### Start

To start the daemon use `python daemon.py start`.

### Stop

To stop the daemon use `python daemon.py stop`.

### Restart

To restart the daemon use `python daemon.py restart`.

### Changing the executable commands

If you don't want a command to execute make sure it isn't in your `commands` file.

If you want to add a command, add a code of this command to the `Daemon` as

```python
def cmd(self, parameters):
	#put your code here
```

Then add this command to the `DaemonCommandsCon` as

```python
def cmd(self, parameters):
	self.__ourdaemon.pingall(parameters)
```

To make sure the command is executed add it to the `commands` file as

```
cmd parameter1 parameter2 ...
```

### Pingall

This command is used to ping all the servers specified in the `/conf/servers.txt` and drop the result in the `/response/ping.csv` file.
