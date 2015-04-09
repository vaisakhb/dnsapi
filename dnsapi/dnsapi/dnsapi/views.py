import json
import os,tempfile
import json,yaml
import subprocess
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


with open("/var/tmp/config.yaml",'r') as f:
	config_yaml=yaml.load(f)

try:
	bind_master=config_yaml["BIND_MASTER"]
	log_file = config_yaml['LOG_FILENAME']
	log_level=config_yaml["LOGLEVEL"]
except KeyError:
	print "Config parameters not found "
	raise SystemExit


LOGGING_LEVELS = { 'debug':logging.DEBUG,
            'info':logging.INFO,
            'warning':logging.WARNING,
            'error':logging.ERROR,
            'critical':logging.CRITICAL,
            }

log_file = config_yaml['LOG_FILENAME']
log_level=config_yaml["LOGLEVEL"]

logging.basicConfig(filename=log_file,
                    level=LOGGING_LEVELS[log_level],
		    format='[%(asctime)s]:%(message)s',
                    )



@csrf_exempt
def get_request(request):
	global remote_user
	remote_user=request.META['REMOTE_USER']	
	if request.method == "POST":
		json_data = request.read()
		try:
			data = json.loads(json_data)
		except ValueError:
			logging.debug("user=%s\nJSON DUMP:%s",remote_user,json.dumps(json_data,indent=4, sort_keys=True))
			return HttpResponse("Invalid Json",status=405)
		r_data,r_code=json2nsupdate(data,remote_user)
                return HttpResponse(r_data,status=r_code)
	else:
		return HttpResponse("Unknown method",status=405)

def json2nsupdate(json_data,user):
	mandate_fields={"add":["name","ttl","class","data"],"delete":["name","class","data"]}
	ops_conv={"delete":"delete","add":"add"}
	try:
		temp = tempfile.NamedTemporaryFile()
		temp.writelines(["server ",bind_master,"\n"])
		for ops in ["delete","add"]:
			if ops_conv[ops] in json_data.keys():
				for item in json_data[ops_conv[ops]]:
					try:
						nsupdate_format="update " + ops_conv[ops]
						for field in mandate_fields[ops]:
							nsupdate_format+=" "+item[field]
					except:
						logging.debug("user=%s\nJSON DUMP:%s",user,json_dumps(json_data,indent=4, sort_keys=True))
						return ("Invalid json",400)
					finally:
						temp.writelines([nsupdate_format.rstrip(),"\n"])
                                     	        if item['class'] is 'A':
							nsupdate_format="update %s %s %s.in-addr.arpa. %s PTR %s"%(ops_conv[ops],'.'.join(reversed(item['data'].split('.'))),item['ttl'],item['name'])
							temp.writelines([nsupdate_format.rstrip(),"\n"])
		temp.writelines(["show","\n","send","\n"])
	except:
		logging.critical("User=%s\nUnknown error %s",user,json_dumps(json_data,indent=4, sort_keys=True))
		return ("Unknown error",500)
	finally:
		temp.flush()
		(nsupdate_out,nsupdate_rc)=run_nsupdate(temp.name,user)
                print "error_code"+str(nsupdate_rc)
		if nsupdate_rc != 0:
			logging.critical("user=%s::Nsudpate error",user)
			return ("Nsupdate error",500)
		return ("Success",200)
		temp.close()

def run_nsupdate(nsupdate_file,user):
        try:
                nsupdate_command="/usr/bin/nsupdate "+nsupdate_file
                pr=subprocess.Popen(["/usr/bin/nsupdate",nsupdate_file],stdin=subprocess.PIPE,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, err = pr.communicate(b"input data that is passed to subprocess' stdin")
                rc = pr.returncode
                logging.debug("user=%s\nNsupdate out::%s",user,output)
                return (output,rc)
        except IOError:
                print "Not able to open the temp file"
        except subprocess.CalledProcessError as nsudpate_exec:
                return ("Error",nsudpate_exec.returncode)
