import sys
import os
import datetime
import time
import atexit
import signal
import pandas as pd
from flask import Flask, render_template
import matplotlib
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import base64
from io import BytesIO

app = Flask(__name__, template_folder='template')

apppidfile = None

pingappcsv = None

pinghistsappcsv = None

@app.route('/')
def index():
	servers_df = pd.DataFrame({"Empty" : []})

	if os.path.isfile(pingappcsv):
		servers_df = pd.read_csv(pingappcsv)

	plot_data = pd.DataFrame({"Time" : [], "Server" : [], "Status" : []})

	if os.path.isfile(pinghistsappcsv):
		plot_data = pd.read_csv(pinghistsappcsv)

	plot_data['Time'] = pd.to_datetime(plot_data['Time'])
	fig = Figure(figsize=(10, 6))
	ax = fig.subplots()
	for server, group in plot_data.groupby('Server'):
		ax.plot(group['Time'], group['Status'], label=server)
	ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
	fig.autofmt_xdate(rotation=45)
	ax.set_yticks([0, 1])
	ax.legend()
	ax.set_title('Server Status Over Time')
	ax.set_xlabel('Time')
	ax.set_ylabel('Status')

	buf = BytesIO()
	fig.savefig(buf, format="png")
	data = base64.b64encode(buf.getbuffer()).decode("ascii")

	return render_template('display_dataframe.html', table=servers_df.to_html(classes='data', index=False), plot_url=f"data:image/png;base64,{data}")



class Daemon:

	def __init__(self, pidfile, commands, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', sleeptime=10):
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile
		self.sleeptime = sleeptime
		self.curdir = os.getcwd()

		local = DaemonCommandsCon(self)
		self.commands = {}
		for command in dir(local):
		    if command[0:1] != '_':
		        self.commands[command]=getattr(local, command)

		self.executions = {}
		cf = open(commands, 'r')
		cd = cf.read().split('\n')
		for cmdline in cd:
			cmd = cmdline.split()
			self.executions[cmd[0]] = cmd[1:]


	def daemonize(self):
		"""
		do the UNIX double-fork magic, see Stevens' "Advanced 
		Programming in the UNIX Environment" for details (ISBN 0201563177)
		http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
		"""
		try: 
		    pid = os.fork() 
		    if pid > 0:
		        # exit first parent
		        sys.exit(0) 
		except OSError as e: 
		    sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
		    sys.exit(1)

		# decouple from parent environment
		os.chdir("/") 
		os.setsid() 
		os.umask(0) 

		# do second fork
		try: 
		    pid = os.fork() 
		    if pid > 0:
		        # exit from second parent
		        sys.exit(0) 
		except OSError as e: 
		    sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
		    sys.exit(1) 

		# redirect standard file descriptors
		sys.stdout.flush()
		sys.stderr.flush()
		si = open(self.stdin, 'r')
		so = open(self.stdout, 'a+')
		se = open(self.stderr, 'a+')
		os.dup2(si.fileno(), sys.stdin.fileno())
		os.dup2(so.fileno(), sys.stdout.fileno())
		os.dup2(se.fileno(), sys.stderr.fileno())

		# write pidfile
		atexit.register(self.delpid)
		pid = str(os.getpid())
		open(self.pidfile,'w+').write("%s\n" % pid)

	def delpid(self):
	    os.remove(self.pidfile)	

	def start(self):
	    """
	    Start the daemon
	    """
	    # Check for a pidfile to see if the daemon already runs
	    try:
	        pf = open(self.pidfile,'r')
	        pid = int(pf.read().strip())
	        pf.close()
	    except IOError:
	        pid = None

	    if pid:
	        message = "pidfile %s already exist. Daemon already running?\n"
	        sys.stderr.write(message % self.pidfile)
	        sys.exit(1)
	    
	    # Start the daemon
	    self.daemonize()
	    self.run()

	def stop(self):
	    """
	    Stop the daemon
	    """
	    # Get the pid from the pidfile
	    try:
	        pf = open(self.pidfile,'r')
	        pid = int(pf.read().strip())
	        pf.close()
	    except IOError:
	        pid = None

	    if not pid:
	        message = "pidfile %s does not exist. Daemon not running?\n"
	        sys.stderr.write(message % self.pidfile)
	        return # not an error in a restart
	        
	    # Try killing the daemon process
	    try:
	        while 1:
	            os.kill(pid, signal.SIGTERM)
	            time.sleep(0.1)	
	    except OSError as err:
	        err = str(err)
	        if err.find("No such process") > 0:
	            if os.path.exists(self.pidfile):
	                os.remove(self.pidfile)
	        else:
	            print(str(err))
	            sys.exit(1)

	def restart(self):
	    """
	    Restart the daemon
	    """
	    self.stop()
	    self.start()

	def appstart(self):
		self.pidfile = apppidfile
		"""
		Start the daemon
		"""
		# Check for a pidfile to see if the daemon already runs
		try:
		    pf = open(self.pidfile,'r')
		    pid = int(pf.read().strip())
		    pf.close()
		except IOError:
			pid = None

		if pid:
		    message = "pidfile %s already exist. Daemon already running?\n"
		    sys.stderr.write(message % self.pidfile)
		    sys.exit(1)

		# Start the daemon
		self.daemonize()
		app.run()

	def appstop(self):
		"""
	    Stop the daemon
	    """
		self.pidfile = apppidfile
		self.stop()

	def apprestart(self):
		"""
		Restart the daemon
		"""
		self.appstop()
		self.appstart()

	def run(self):
		while True:
			for command in self.executions:
				try:
					self.commands[command](*self.executions[command])

				except TypeError as error:
					print(error)

			time.sleep(self.sleeptime)

	def pingall(self, servers, outcsv, histtime):
		out = {"Time" : [], "Server" : [], "Status" : []}
		if not os.path.isfile(self.curdir + outcsv):
			pd.DataFrame(out).to_csv(self.curdir + outcsv, index=False)
		if not os.path.isfile(pinghistsappcsv):
			pd.DataFrame(out).to_csv(pinghistsappcsv, index=False)
		param = '-c'
		with open(self.curdir + servers, 'r') as f:
			servers = f.read().split()
		for server in servers:
			response = os.system(f"ping {param} 1 {server}")
			out['Time'].append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
			out['Server'].append(server)
			if response == 0:
				out['Status'].append(1)
			else:
				out['Status'].append(0)
		servers_df = pd.DataFrame(out)
		servers_df.to_csv(self.curdir + outcsv, mode='a', index=False, header=False)
		servers_df_hist = pd.read_csv(pinghistsappcsv)
		servers_df_hist = servers_df_hist[pd.to_datetime(servers_df_hist['Time']) >= pd.to_datetime(datetime.datetime.now() - datetime.timedelta(seconds=int(histtime)))]
		servers_df_hist.to_csv(pinghistsappcsv, index=False)
		servers_df.to_csv(pinghistsappcsv, mode='a', index=False, header=False)
		servers_df.to_csv(pingappcsv, index=False)


class ReactFunctionCon:

	def __init__(self, ourdaemon):
	    self.__ourdaemon = ourdaemon

	def start(self):
	    self.__ourdaemon.start()

	def stop(self):
	    self.__ourdaemon.stop()
	    
	def restart(self):
	    self.__ourdaemon.restart()

	def appstart(self):
		self.__ourdaemon.appstart()

	def appstop(self):
		self.__ourdaemon.appstop()

	def apprestart(self):
		self.__ourdaemon.apprestart()

class DaemonCommandsCon:

	def __init__(self, ourdaemon):
	    self.__ourdaemon = ourdaemon

	def pingall(self, servers, outcsv, histtime):
	    self.__ourdaemon.pingall(servers, outcsv, histtime)

def GetReacts(daemon):
	local = ReactFunctionCon(daemon)
	reacts = {}
	for react in dir(local):
	    if react[0:1] != '_':
	        reacts[react] = getattr(local, react)
	return reacts


if __name__ == "__main__":

	pidfile = os.getcwd() + "/conf/daemon-naprimer.pid"

	apppidfile = os.getcwd() + "/conf/app-daemon.pid"

	commands = os.getcwd() + "/conf/commands.txt"

	stdin = "/dev/null"

	stdout = "/dev/null"

	stderr = os.getcwd() + "/conf/stderr.err"

	pingappcsv = os.getcwd() + "/conf/ping.csv"

	pinghistsappcsv = os.getcwd() + "/conf/pinghist.csv"

	sleeptime = 10

	daemon = Daemon(pidfile, commands, stdin, stdout, stderr, sleeptime)

	reacts = GetReacts(daemon)

	if len(sys.argv) > 1:

		if sys.argv[1] in iter(reacts):

			try:
				reacts[sys.argv[1]](*sys.argv[2:len(sys.argv)])
				sys.exit(0)

			except TypeError as error:
				print(error)
				sys.exit(2)
		else:

			print("usage: %s %s" % (sys.argv[0], reacts))
			sys.exit(2)
