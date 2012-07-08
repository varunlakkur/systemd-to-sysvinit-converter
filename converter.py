
'''
 @author: Akhil Vij
'''

import ConfigParser
import sys
from types import StringType

class newdict(dict):
	def __setitem__(self, key, value):
		if key in self:
			if type(value) is not StringType:
				dict.__setitem__(self, key, self[key] + value)
		else:
			if type(value) is StringType:
				temp_list = []
				temp_list.append(value)
				value = temp_list
			dict.__setitem__(self, key, value)

def parser_init():
	global config
	config = ConfigParser.ConfigParser(None, newdict)
	if len(sys.argv) == 2:
		if not config.read(sys.argv[1]):
			print "Unable to parse file", sys.argv[1]
			sys.exit(2)
			return;
		global prog
		prog = (sys.argv[1].split('/')[-1]).split('.')[0]
	else:
		print "Usage: python code.py /location/of/systemd/conf_file"
		sys.exit(2)

def add_description():
	if config.has_option("Unit", "Description"):
		print "Short-Description: " + config.get("Unit", "Description")[0]

def add_runlevels():
	if config.has_option("Install", "WantedBy"):
			runlevel = config.get("Install", "WantedBy")[0]
			if runlevel == "multi-user.target":
				print "Default-Start:\t2 3 4"
				print "Default-Stop:\t0 1 6"
				return 4

			elif runlevel == "graphical.target":
				print "Default-Start:\t2 3 4 5"
				print "Default-Stop:\t0 1 6??"
				return 5

# Not sure about basic.target & rescue.target : 
# check once - 
# https://fedoraproject.org/wiki/User:Johannbg/QA/Systemd/Systemd.special

			elif runlevel == "basic.target":
				print "Default-Start:\t1"
				print "Default-Stop:\t??"
				return 1

			elif runlevel == "rescue.target":
				print "Default-Start:\t1"
				return 1

			else:
				return

def add_required_service():
	required_str = "Required-Start:\t"
	remote_fs_flag = True
	syslog_flag = True
	network_flag = True
	local_fs_flag = True
	rpcbind_flag = True
	nsslookup_flag = True
	options = ['After', 'Requires']

	for option in options:
		if config.has_option("Unit", option):
			after_services_str = config.get("Unit", option)[0]
			for unit in after_services_str.split(" "):
				if unit == "syslog.target" and syslog_flag:
					required_str = required_str + "$syslog "
					syslog_flag = False
				elif (unit == "remote-fs.target" or unit == 
					"proc-fs-nfsd.mount" or unit == 
					"var-lib-nfs-rpc_pipefs.mount") and remote_fs_flag:
					required_str = required_str + "$remote_fs "
					remote_fs_flag = False
				elif unit == "network.target" and network_flag:
					required_str = required_str + "$network "
					network_flag = False
				elif unit == "local_fs.target" and local_fs_flag:
					required_str = required_str + "$local_fs "
					local_fs_flag = False
				elif unit == "rpcbind.service" and rpcbind_flag:
					required_str = required_str + "$portmap "
					rpcbind_flag = False
				elif unit == "nss-lookup.target" and nsslookup_flag:
					required_str = required_str + "$named "
					nsslookup_flag = False
		else:
			break

	print required_str

def add_should_service():
	should_str = "Should-Start:\t"
	remote_fs_flag = True
	syslog_flag = True
	network_flag = True
	local_fs_flag = True
	rpcbind_flag = True
	options = ['Wants']
	for option in options:
		if config.has_option("Unit", option):
			after_services_str = config.get("Unit", option)[0]
			for unit in after_services_str.split(" "):
				if unit == "syslog.target" and syslog_flag:
					should_str = should_str + "$syslog "
					syslog_flag = False
				elif (unit == "remote-fs.target" or unit == 
					"proc-fs-nfsd.mount" or unit == 
					"var-lib-nfs-rpc_pipefs.mount") and remote_fs_flag:
					should_str = should_str + "$remote_fs "
					remote_fs_flag = False
				elif unit == "network.target" and network_flag:
					should_str = should_str + "$network "
					network_flag = False
				elif unit == "local_fs.target" and local_fs_flag:
					should_str = should_str + "$local_fs "
					local_fs_flag = False
				elif unit == "rpcbind.service" and rpcbind_flag:
					should_str = should_str + "$portmap"
					rpcbind_flag = False
		else:
			break
	print should_str

def check_env_file(Environment_file):
	print "if test -f", Environment_file, "; then\n\t.", Environment_file,
	print "\nfi\n"
					
def add_provides():
	print "Provides:", prog

def build_LSB_header(): #add more arguments here
	print "### BEGIN INIT INFO"
# Call functions here for Provides, Required-Start, Required-Stop,
# Default-Start, Default-Stop, Short-Description and Description. Don't know
# whether we can get all the info for this from the "Unit" Section alone.
	add_provides()
	add_required_service()
	add_should_service()
	add_runlevels()
	add_description()
	print "### END INIT INFO"

def exec_path():
	'''
	Function: exec_path()
	---------------------
	Uses the ExecStart option to fetch the daemon's executable path
	
	@return: The daemon's executable
	 
	'''
	if config.has_option("Service", "ExecStart"):
		return clear_dash_prefix(config.get("Service",
										"ExecStart")[0]).split()[0]
	return ""

def clear_dash_prefix(exec_str):
	'''
	Function: clear_dash_prefix(string)
	--------------------------------------
	removes the '-' prefix from the argument.
	
	@param str: string which needs the cleanup
	@return: Returns the string after removing the string.
	'''
	if exec_str[0] == '-':
		return exec_str[1:len(exec_str)]
	return exec_str
	
def bash_check_for_success(action, r_val=1):
	''' 
	Function: bash_check_for_success(action, return_value = 1)
	----------------------------------------------------------
	This functions is used to check the return value of every command executed
	in the init script. The syntax is simple.
		
	@param action: start, stop etc.
	@param return_val: The value used for "exit" when the check fails.	
	@return: It simply prints a few statements to STDOUT. No return value.: 
	'''
	print "\tif [ $? -ne 0 ]; then"
	print "\t\techo \"Unable to " + action + " $prog\"\n\t\texit " + str(r_val)
	print "\tfi"
		
def timeout(action):
	'''
	Function: timeout(prog_path, action)
	------------------------------------
	checks whether the "action" performed is completed in a given timeout period.
	
	@param action: start, stop etc.
	@return: It simply prints a few statements to STDOUT. No return value.
	'''	
	if config.has_option("Service", "TimeoutSec"):
		if config.get("Service", "TimeoutSec")[0] == "0":
			bash_check_for_success(action)
		else:
			print "\tTIMEOUT = $STARTTIMEOUT"
			print "\tTEMPPID = pidofproc", exec_path()
			print "\twhile [ TIMEOUT -gt 0 ]; do"
			if action == "start":
				print "\t\tif ! /bin/kill -0 $TEMPPID ; then"
				print "\t\t\techo $prog started successfully\""
			elif action == "stop":
				print "\t\tif /bin/kill -0 $TEMPPID ; then"
				print "\t\t\techo $prog stopped successfully\""
			print "\t\t\tbreak"
			print "\t\tfi"
			print "\t\tsleep 1"
			print "\t\tlet TIMEOUT=${TIMEOUT} - 1"
			print "\tdone\n"
			print "\tif [ $TIMEOUT -eq 0 ]; then"
			# Send a SIGTERM signal and if timed out again, kill it
			if action == "stop":
				print "\t\tTIMEOUT = $STARTTIMEOUT"
				print "\t\tkill -15 $TEMPPID"
				print "\t\twhile [ TIMEOUT -gt 0 ]; do"
				print "\t\t\tif /bin/kill -0 $TEMPPID ; then"
				print "\t\t\t\techo $prog terminated successfully\""
				print "\t\t\t\tbreak"
				print "\t\t\tfi"
				print "\t\t\tsleep 1"
				print "\t\t\tlet TIMEOUT=${TIMEOUT} - 1"
				print "\t\tdone\n"
				print "\t\tif [ $TIMEOUT -eq 0 ]; then"
				print "\t\t\tkill -9 $TEMPPID"
				print "\t\t\techo \"$prog killed\""
				print "\t\tfi"
			else:
				print "\t\techo \"Timeout error occurred trying to", action,
				print "$prog\"\n\tfi"
	else:
		bash_check_for_success(action)

def build_start():
	print "start() {\n\techo - n \"Starting $prog: \""

	if config.has_option("Service", "ExecStartPre"):
		if len(config.get("Service", "ExecStartPre")) == 1:
			start_pre_list = config.get("Service",
									"ExecStartPre")[0].split(';')
		else:
			start_pre_list = config.get("Service", "ExecStartPre")
		for start_pre in start_pre_list:
			print "\tstart_daemon", clear_dash_prefix(start_pre)
			if start_pre[0] != "-":
				bash_check_for_success("start")
		
	if config.has_option("Service", "ExecStart"):
		start_list = config.get("Service", "ExecStart")
		if config.has_option("Service", "Type"):
			if config.get("Service", "Type")[0].lower() == "oneshot":
				if len(config.get("Service", "ExecStart")) == 1:
					start_list = config.get("Service",
										"ExecStart")[0].split(';')
		for exec_start in start_list:
			if config.has_option("Service", "PIDFile"):
				print "\tstart_daemon " + "-p $PIDFILE",
				print clear_dash_prefix(exec_start)
			else:
				print "\tstart_daemon " + clear_dash_prefix(exec_start)
		
		timeout("start")
			
	if config.has_option("Service", "ExecStartPost"):
		if len(config.get("Service", "ExecStartPost")) == 1:
			start_post_list = config.get("Service",
									"ExecStartPost")[0].split(';')
		else:
			start_post_list = config.get("Service", "ExecStartPost")
		for start_post in start_post_list:
			print "\tstart_daemon", clear_dash_prefix(start_post)
			if start_post[0] != "-":
				bash_check_for_success("start")
	print "}\n"

def build_stop():
	'''
	The behaviour of build_stop is based on the option "killmode"
	=> control-group - This is the default. In this case, the ExecStop is
	executed first and then rest of the processes are killed.
	=> process - Only the main process is killed.
	=> none - The ExecStop command is run and no process is killed.
	
	Since, we don't have the concept of control group in sysV, we simply run
	ExecStop and kill all the remaining processes. The signal for killing is
	derived from "KillSignal" option.
	'''
	print "stop() {\n\techo -n \"Stopping $prog: \""
	
	if config.has_option("Service", "ExecStop"):
		if len(config.get("Service", "ExecStop")) == 1:
			stop_list = config.get("Service",
									"ExecStop")[0].split(';')
		else:
			stop_list = config.get("Service", "ExecStop")
		for exec_stop in stop_list:
			print "\t", clear_dash_prefix(exec_stop)
		timeout("stop")
		
	else:
		if config.has_option("Service", "PIDFile"):
			if config.has_option("Service", "KillSignal"):
				print "\tkillproc -p $PIDFILE -s",
				print config.get("Service", "KillSignal")[0], exec_path()
			else:
				print "\tkillproc -p $PIDFILE ", exec_path()
		else:
			if config.has_option("Service", "KillSignal"):
				print "\tkillproc -s", config.get("Service", "KillSignal")[0],
				print exec_path()
		
		timeout("stop")

	if config.has_option("Service", "ExecStopPost"):
		if len(config.get("Service", "ExecStopPost")) == 1:
			stop_post_list = config.get("Service",
									"ExecStopPost")[0].split(';')
		else:
			stop_post_list = config.get("Service", "ExecStopPost")
		for stop_post in stop_post_list:
			print "\t", clear_dash_prefix(stop_post)
			if stop_post[0] != "-":
				bash_check_for_success("stop")
	print "}\n"

def build_reload():
	""" 
	This functions generates the reload() bash function. Here is how it works:
	- If ExecReload statement already exists then it'll be executed.
	- If there is no ExecReload then we need to find the service's PID. For 
	that, the function checks for pidfile and call "pidofproc -p $PIDFILE" 
	else it'll find the service's executable through ExecStart and execute 
	"pidofproc /path/to/executable". Since, ExecStart is mandatory for every
	service, obtaining path is easy and reliable.
	"""
	print "reload () {\n\techo -n \"Reloading $prog: \""
	if config.has_option("Service", "ExecReload"):
		if len(config.get("Service", "ExecReload")) == 1:
			reload_list = config.get("Service", "ExecReload")[0].split(';')
		else:
			reload_list = config.get("Service", "ExecReload")
		for exec_reload in reload_list:
			print "\t", clear_dash_prefix(exec_reload)
			if exec_reload[0] != "-":
				bash_check_for_success("reload")
						
	else:
		if config.has_option("Service", "PIDFile"):
			print "\tPID = pidofproc -p $PIDFILE"
		
		else:
				print "\tPID = pidofproc", exec_path()
		print "\tif [ $PID -eq 1 -o $PID -eq 2 -o $PID -eq 3 ] then"
		print "\t\techo \"Unable to Reload - Service is not running\"\n\tfi" 
		print "\tkill -HUP $PID"
	print "}\n"

def build_default_params():
	''' This file is included to comply with lsb guidelines.'''
	print "\n. /lib/lsb/init-functions\n"
	print "prog=" + prog

	if config.has_option("Service", "EnvironmentFile"):
		check_env_file(config.get("Service", "EnvironmentFile")[0]);

	if config.has_option("Service", "PIDFile"):
		print "PIDFILE={PIDFILE:-"+ config.get("Service", "PIDFile")[0]+"}"
	
	if config.has_option("Service", "KillMode"):
		print "SIG={SIG:-" + config.get("Service", "KillMode")[0]+"}"
		
	if config.has_option("Service", "TimeoutSec"):
		timeout = config.get("Service", "TimeoutSec")[0]
		if timeout != "0":
			print "STARTTIMEOUT=", config.get("Service", "TimeoutSec")[0]
			
	print

def build_call_arguments():
	print """case "$1" in"""
	print "\tstart)\n\t\tstart\n\t\t;;"
	print "\tstop)\n\t\tstop\n\t\t;;"
	print "\treload)\n\t\treload\n\t\t;;"
	print "\trestart)\n\t\tstop\n\tstart\n\t\t;;"
	print "\t* )\n\t\techo $\"Usage: $prog",
	print "{start|stop|reload|restart|status}\""
	print "esac\n"

# The build_{start,stop,reload} functions will be called irrespective of the
# existence of Exec{Start,Stop,Reload} options. This is to ensure that all the
# basic call exists(even if they have no operation).

parser_init()
build_LSB_header()
build_default_params()
build_start()
build_stop()
build_reload()
build_call_arguments()
