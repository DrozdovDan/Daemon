# DAEMON

Current daemon can be used to periodically execute several commands in the background of an Unix system.

It also can start a web app using Flask.

## Installation

Use `git clone` to get your local version of the daemon.

## Usage

Before start this daemon make sure to install all requirements using `pip install -r requirements.txt`.

You can manage your own configs of daemon by changing the default settings:
```python
pidfile = os.getcwd() + "/conf/daemon-naprimer.pid"

apppidfile = os.getcwd() + "/conf/app-daemon.pid"

commands = os.getcwd() + "/conf/commands.txt"

stdin = "/dev/null"

stdout = "/dev/null"

stderr = os.getcwd() + "/conf/stderr.err"

pingappcsv = os.getcwd() + "/conf/ping.csv"

sleeptime = 10
```

### Start

To start the daemon use `python daemon.py start`.

### Stop

To stop the daemon use `python daemon.py stop`.

### Restart

To restart the daemon use `python daemon.py restart`.

### Start the web app

To start the web app use `python daemon.py appstart`.

### Stop

To stop the web app use `python daemon.py appstop`.

### Restart

To restart the web app use `python daemon.py apprestart`.

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

This command is used to ping all the servers specified in the `/conf/servers.txt` and append the result in the `/response/ping.csv` file.

It also drop the result in `/conf/ping.csv`, which is being used by web app.

### Web app

This app display the last results of `pingall` command executed by daemon and draw a graph of all results of `pingall` command executed by daemon.
Default server: localhost:5000
