#!/usr/bin/python

import time
import datetime
import getopt
import sys

type_os = "os"
type_mysql = "mysql"
type_redis = "redis"
support_types=[type_os,type_mysql,type_redis]

service_type=type_os

output_type = 0 #0 is print, 1 is file.
output_file_name = ""
output_file = None
output_file_by_day = 0
date_format = "%Y-%m-%d"
current_day = str(time.strftime(date_format, time.localtime()))

host="127.0.0.1"
port=3306
user="root"
password=""

interval=1 #second

#column_format = '%-*s'
column_format = '%*s'

segmentation_line_len = 40

####### Util #######
def byte2readable(bytes):
    bytes_float = float(bytes)
    if bytes_float > -1024.0 and bytes_float < 1024.0:
        if (str(bytes).find(".") >= 0):
            return "%3.1f"%bytes_float
        else:
            return str(bytes)
    else:
        bytes_float /= 1024.0

    for count in ['K', 'M', 'G']:
        if bytes_float > -1024.0 and bytes_float < 1024.0:
            return "%3.1f%s" % (bytes_float, count)

        bytes_float /= 1024.0

    return "%3.1f%s" % (bytes_float, 'T')

def num2readable(number):
    number_float = float(number)
    if number_float > -1000.0 and number_float < 1000.0:
        if (str(number).find(".") >= 0):
            return "%3.2f"%number_float
        else:
            return str(number)
    else:
        number_float /= 1000.0

    for count in ['k', 'm', 'g']:
        if number_float > -1000.0 and number_float < 1000.0:
            return "%3.2f%s" % (number_float, count)

        number_float /= 1000.0

    return "%3.2f%s" % (number_float, 't')

def microsecond_differ_by_datetime(datetime_new, datetime_old):
    datetime_differ = datetime_new - datetime_old
    return datetime_differ.days*24*3600*1000000 + datetime_differ.seconds*1000000 + datetime_differ.microseconds

def output(content):
    if (output_type == 0):
        print content
    elif (output_type == 1):
        output_file.write(content + '\n')
    else:
        return

    return

def separate_output_file_if_needed():
    if (output_file_by_day == 1):
        today = str(time.strftime(date_format, time.localtime()))
        global current_day
        global output_file
        if current_day != today:
            current_day = today
            if (output_file.closed == False):
                output_file.close()

            output_file = open(output_file_name+'_'+current_day, 'a', 0)
            return 1

    return 0

####### Class StatusSection #######
class StatusSection:
    def __init__(self, name, columns, status_get_functions, instructions):
        self.name = name
        self.columns = columns
        self.status_get_functions = status_get_functions
        self.instructions = instructions

    def getName(self):
        return self.name
    def getColumns(self):
        return self.columns
    def getInstructions(self):
        return self.instructions

    def getHeader(self):
        len_total = 0
        for column in self.columns:
            len_total += column.getWidth()

        if (len(self.name) == 0):
            return ' '*len_total

        len_half_left = (len_total-len(self.name))/2
        len_half_right = len_half_left
        if ((len_total-len(self.name))%2 == 1):
            len_half_right += 1

        return '-'*len_half_left+self.name+'-'*len_half_right

####### Class StatusColumn #######
column_flags_none=int('0000',2)  # None flags.
column_flags_rate=int('0001',2)  # The column is shown as rate.
column_flags_bytes=int('0010',2)  # The column is shown as bytes.
column_flags_string=int('0100',2)  # The fields are strings, otherwise are numbers; string can't be column_flags_rate.
column_flags_ratio=int('1000',2)  # The column is shown as ratio.
class StatusColumn:
    def __init__(self, name, blanks, flags, field_handler, fields, instructions):
        self.name = name
        self.flags = flags
        self.field_handler = field_handler
        self.fields = fields
        self.instructions = instructions
        self.value_old = 0
        self.obj_old = None
        if (blanks > 0):   # Blanks is bigger than zero means we really want the blanks.
            self.width = len(name) + blanks
        elif (blanks == 0):   # Blanks is zero means the default blanks count between the columns, default is 2.
            self.width = len(name) + 2
            if (self.width < 8):
                self.width = 8
        else:
            self.width = len(name) + 2

    def getName(self):
        return self.name
    def getWidth(self):
        return self.width
    def getFlags(self):
        return self.flags
    def getFields(self):
        return self.fields
    def getInstructions(self):
        return self.instructions

    def getValueOld(self):
        return self.value_old
    def getObjOld(self):
        return self.obj_old

    def getHeader(self):
        return column_format % (self.getWidth(), self.getName())

    def getValue(self, column, status):
        return column.field_handler(column, status)

    def setValueOld(self, value):
        self.value_old = value
    def setObjOld(self, obj):
        self.obj_old = obj

def field_handler_common(column, status):
    if (column.getFlags()&column_flags_ratio):
        fields = column.getFields()
        return "%.3f%%"%(float(status[fields[0]])*100/float(status[fields[1]]))

    value_num = 0
    value_str = ''
    for field in column.getFields():
        if (column.getFlags()&column_flags_string):
            if (len(value_str) == 0):
                value_str = str(status[field])
            else:
                value_str += ',' + str(status[field])
        else:
            value_num += long(status[field])

    if (column.getFlags()&column_flags_rate):
        rate = value_num - column.getValueOld()
        column.setValueOld(value_num)
        if (interval > 1):
            rate = float(rate)/interval
            value_str = "%3.1f"%rate
        else:
            value_str = str(rate)
    else:
        if (column.getFlags()&column_flags_string == 0):
            value_str = str(value_num)

    if (column.getFlags()&column_flags_bytes):
        return byte2readable(value_str)
    elif (column.getFlags()&column_flags_string == 0):
        value_str = num2readable(value_str)

    return value_str

def get_status_line(sections, status):
    line = ""
    for section in sections:
        for column in section.getColumns():
            line += column_format % (column.getWidth(), column.getValue(column, status))
        line += '|'
    return line

####### Common #######
def getSupportedServiceTypesName():
    names = ''
    count = len(support_types)
    for type in support_types:
        names += type
        count -= 1
        if (count >= 1):
            names += ","

    return names

def get_sections_header(sections):
    header = ''
    for section in sections:
        header += section.getHeader()
        header += ' '

    return header

def get_columns_header(sections):
    header = ''
    for section in sections:
        for column in section.getColumns():
            header += column.getHeader()

        header += '|'

    return header

def get_section_instructions_old(section):
    segmentation_line = "-" * segmentation_line_len
    instructions = "Section| " + section.getName() + " : " + section.getInstructions()
    instructions += "\n" + segmentation_line
    columns = section.getColumns()
    for column in columns:
        instructions += "\n"
        instructions += "Column | " + column.getName() + " : " + column.getInstructions()

    return instructions

def divide_one_line_to_multi_lines_by_max_length(line, max_len):
    lines = []

    if len(line) <= max_len:
        lines.append(line)
        return lines

    line_part = ""
    fields = line.split()
    count = 0
    for field in fields:
        if (len(line_part)+1+len(field)) > max_len:
            lines.append(line_part)
            line_part = ""

        if (count >= 1):
            line_part += " "

        line_part += field
        count += 1

    if (len(line_part.lstrip()) > 0):
        lines.append(line_part)

    return lines

def get_one_instructions(header, name, instructions, max_line_len):
    line = name + " : " + instructions
    lines = divide_one_line_to_multi_lines_by_max_length(line, max_line_len)

    one_instructions = header + "|" + lines[0]
    for line in lines[1:]:
        one_instructions += "\n"
        one_instructions += " " * len(header) + "|" + line

    return one_instructions

def get_section_instructions(section):
    max_line_len = 60
    header_section = "Section"
    header_column = "Column "

    section_instructions = get_one_instructions(header_section, section.getName(), section.getInstructions(), max_line_len)

    section_instructions += "\n" + "-"*segmentation_line_len + "\n"
    columns = section.getColumns()
    count = len(columns)
    for column in columns:
        section_instructions += get_one_instructions(header_column, column.getName(), column.getInstructions(), max_line_len)
        count -= 1
        if (count >= 1):
            section_instructions += "\n" #+ "-"*segmentation_line_len + "\n"

    return section_instructions

def field_handler_time(column, status):
    return column_format % (9, time.strftime("%H:%M:%S", time.localtime()))

time_section = StatusSection("time", [
StatusColumn("Time", 5, column_flags_string, field_handler_time, [], "Show the time when the status display.")
],[],"os time")

def get_os_cpu_status(server, status):
    file = open("/proc/stat", 'r')
    line = file.readline()
    file.close()

    # cpu   1-user  2-nice  3-system 4-idle   5-iowait  6-irq   7-softirq
    # cpu   628808  1642    61861    24978051 22640     349     3086        0
    os_cpu_status = line.split()
    status["os_cpu_usr"] = int(os_cpu_status[1]) + int(os_cpu_status[2])
    status["os_cpu_sys"] = int(os_cpu_status[3]) + int(os_cpu_status[6]) + int(os_cpu_status[7])
    status["os_cpu_idl"] = int(os_cpu_status[4])
    status["os_cpu_iow"] = int(os_cpu_status[5])
    status["os_cpu_total"] = status["os_cpu_usr"] + status["os_cpu_sys"] + status["os_cpu_idl"] + status["os_cpu_iow"]

    return

def field_handler_os_cpu(column, status):
    fields = column.getFields()
    value = status[fields[0]]
    total = status[fields[1]]
    obj = column.getObjOld()
    if (obj == None):
        column.setObjOld([value,total])
        return '0'

    value_diff = value - obj[0]
    total_diff = total - obj[1]
    column.setObjOld([value, total])
    return "%3.1f"%(float(value_diff)/float(total_diff) * 100)

os_cpu_section = StatusSection("os_cpu", [
StatusColumn("usr", 2, column_flags_rate, field_handler_os_cpu, ["os_cpu_usr","os_cpu_total"], "Percentage of cpu user+nice time."),
StatusColumn("sys", 2, column_flags_rate, field_handler_os_cpu, ["os_cpu_sys","os_cpu_total"], "Percentage of cpu system+irq+softirq time."),
StatusColumn("idl", 3, column_flags_rate, field_handler_os_cpu, ["os_cpu_idl","os_cpu_total"], "Percentage of cpu idle time."),
StatusColumn("iow", 2, column_flags_rate, field_handler_os_cpu, ["os_cpu_iow","os_cpu_total"], "Percentage of cpu iowait time.")
],[get_os_cpu_status],
"os cpu status, collect from /proc/stat file")

def get_os_load_status(server, status):
    file = open("/proc/loadavg", 'r')
    line = file.readline()
    file.close()

    os_load_status = line.split()
    status["os_load_one"] = os_load_status[0]
    status["os_load_five"] = os_load_status[1]
    status["os_load_fifteen"] = os_load_status[2]

    return

os_load_section = StatusSection("os_load", [
StatusColumn("1m", 4, column_flags_string, field_handler_common, ["os_load_one"], "One minute average active tasks."),
StatusColumn("5m", 4, column_flags_string, field_handler_common, ["os_load_five"], "Five minute average active tasks."),
StatusColumn("15m", 3, column_flags_string, field_handler_common, ["os_load_fifteen"], "Fifteen minute average active tasks.")
],[get_os_load_status],
"os cpu average load status, collect from /proc/loadavg file")

def get_os_swap_status(server, status):
    count = 0
    file = open("/proc/vmstat", 'r')
    line = file.readline()
    while line:
        if (line.startswith("pswpin")):
            swaps = line.split()
            status["os_swap_pswpin"] = swaps[1]
            count += 1
        elif (line.startswith("pswpout")):
            swaps = line.split()
            status["os_swap_pswpout"] = swaps[1]
            count += 1

        line = file.readline()
        if (count >= 2):
            break

    file.close()
    return

os_swap_section = StatusSection("os_swap", [
StatusColumn("si", 4, column_flags_rate, field_handler_common, ["os_swap_pswpin"], "Counts per second of data moved from memory to swap, related to pswpin."),
StatusColumn("so", 4, column_flags_rate, field_handler_common, ["os_swap_pswpout"], "Counts per second of data moved from swap to memory, related to pswpout.")
],[get_os_swap_status],
"os swap status, collect from /proc/vmstat file")

net_face_name="lo"
def get_os_net_status(server, status):
    file = open("/proc/net/dev", 'r')
    line = file.readline().lstrip()
    
    while line:
        if (line.startswith(net_face_name+':')):
            fields = line.split()
            status["os_net_bytes_in"] = fields[1]
            status["os_net_bytes_out"] = fields[9]
            status["os_net_packages_in"] = fields[2]
            status["os_net_packages_out"] = fields[10]
            break
        
        line = file.readline().lstrip()

    file.close()
    return

os_net_bytes_section = StatusSection("os_net_bytes", [
StatusColumn("in", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["os_net_bytes_in"], "Bytes per second the network incoming."),
StatusColumn("out", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["os_net_bytes_out"], "Bytes per second the network outgoing.")
],[get_os_net_status],
"os network bytes status, collect from /proc/net/dev file, you need to use --net-face option "
"to set the net face name that you want to monitor, the net face name is in the /proc/net/dev file")

os_net_packages_section = StatusSection("os_net_packages", [
StatusColumn("in", 0, column_flags_rate, field_handler_common, ["os_net_packages_in"], "Packages per second the network incoming."),
StatusColumn("out", 0, column_flags_rate, field_handler_common, ["os_net_packages_out"], "Packages per second the network outgoing.")
],[get_os_net_status],
"os network packages status, collect from /proc/net/dev file, you need to use --net-face option "
"to set the net face name that you want to monitor, the net face name is in the /proc/net/dev file")

disk_name = "vda"
os_disk_stats_first_time=1
def get_disk_status(server, status):
    file = open("/proc/diskstats", 'r')
    os_disk_stats_get_time = datetime.datetime.utcnow()
    line = file.readline()

    while line:
        fields = line.split()
        if (fields[2] == disk_name):
            global os_disk_stats_first_time
            if (os_disk_stats_first_time == 1):
                os_disk_stats_first_time = 0
                server.os_disk_stats_fields_old = fields
                server.os_disk_stats_get_time_old = os_disk_stats_get_time

                status["os_disk_reads"] = "0"
                status["os_disk_writes"] = "0"
                status["os_disk_read_bytes"] = "0"
                status["os_disk_write_bytes"] = "0"
                status["os_disk_queue"] = "0"
                status["os_disk_wait"] = "0"
                status["os_disk_service_time"] = "0"
                status["os_disk_busy"] = "0"
                break

            fields_old =  server.os_disk_stats_fields_old

            rd_ios = long(fields[3]) - long(fields_old[3])   #/* Read I/O operations */
            rd_merges = long(fields[4]) - long(fields_old[4])   #/* Reads merged */
            rd_sectors = long(fields[5]) - long(fields_old[5])  #/* Sectors read */
            rd_ticks = long(fields[6]) - long(fields_old[6])    #/* Time in queue + service for read */
            wr_ios = long(fields[7]) - long(fields_old[7])   # /* Write I/O operations */
            wr_merges = long(fields[8]) - long(fields_old[8])  # /* Writes merged */
            wr_sectors = long(fields[9]) - long(fields_old[9]) # /* Sectors written */
            wr_ticks = long(fields[10]) - long(fields_old[10])  # /* Time in queue + service for write */
            ticks = long(fields[12]) - long(fields_old[12])         #/* Time of requests in queue */
            aveq = long(fields[13]) - long(fields_old[13])    #/* Average queue length */

            deltams = microsecond_differ_by_datetime(os_disk_stats_get_time, server.os_disk_stats_get_time_old)
            deltams = float(deltams)/1000

            server.os_disk_stats_fields_old = fields
            server.os_disk_stats_get_time_old = os_disk_stats_get_time

            n_ios = long(rd_ios) + long(wr_ios) #/* Number of requests */
            n_ticks = long(rd_ticks) + long(wr_ticks) #/* Total service time */
            n_kbytes = (float(rd_sectors) + float(wr_sectors))/2.0   #/* Total kbytes transferred */
            queue = float(aveq)/deltams #/* Average queue */
            if (n_ios > 0):
                size = float(n_kbytes)/n_ios   #/* Average request size */
                wait = float(n_ticks)/n_ios    #/* Average wait */
                svc_t = float(ticks)/n_ios     #/* Average disk service time */
            else:
                size = 0
                wait = 0
                svc_t = 0

            busy = 100.0 * float(ticks)/float(deltams)  #/* Utilization at disk (percent) */
            if (busy > 99.99):
                busy = 100

            rkbs = 1000.0*float(rd_sectors)/deltams/2
            wkbs = 1000.0*float(wr_sectors)/deltams/2

            # r/s  w/s
            rd_ios_s = 1000.0 * float(rd_ios)/deltams
            wr_ios_s = 1000.0 * float(wr_ios)/deltams

            status["os_disk_reads"] = num2readable(rd_ios_s if rd_ios_s > 0 else 0)
            status["os_disk_writes"] = num2readable(wr_ios_s if wr_ios_s > 0 else 0)
            status["os_disk_read_bytes"] = byte2readable(rkbs*1024.0 if rkbs > 0 else 0)
            status["os_disk_write_bytes"] = byte2readable(wkbs*1024.0 if wkbs > 0 else 0)
            status["os_disk_queue"] = num2readable(queue if queue > 0 else 0)
            status["os_disk_wait"] = num2readable(wait if wait > 0 else 0)
            status["os_disk_service_time"] = num2readable(svc_t if svc_t > 0 else 0)
            status["os_disk_busy"] = num2readable(busy if busy > 0 else 0)
            break


        line = file.readline()

    file.close()
    return

os_disk_section = StatusSection("os_disk", [
StatusColumn("reads", 0, column_flags_string, field_handler_common, ["os_disk_reads"], "Counts per second read from the disk."),
StatusColumn("writes", 0, column_flags_string, field_handler_common, ["os_disk_writes"], "Counts per second write to the disk."),
StatusColumn("rbytes", 0, column_flags_string, field_handler_common, ["os_disk_read_bytes"], "Bytes per second read from the disk."),
StatusColumn("wbytes", 0, column_flags_string, field_handler_common, ["os_disk_write_bytes"], "Bytes per second write to the disk."),
StatusColumn("queue", 2, column_flags_string, field_handler_common, ["os_disk_queue"], "Disk queue length per second."),
StatusColumn("await", 2, column_flags_string, field_handler_common, ["os_disk_wait"], "Average milliseconds of queue and service time for each read/write."),
StatusColumn("svctm", 2, column_flags_string, field_handler_common, ["os_disk_service_time"], "Average milliseconds of service time for each read/write."),
StatusColumn("%util", 1, column_flags_string, field_handler_common, ["os_disk_busy"], "Disk utilization percent.")
],[get_disk_status],
"os disk status, collect from /proc/diskstats file, you need to use --disk-name option "
"to set the disk name that you want to monitor, the disk name is in the /proc/diskstats file")

def get_os_mem_status(server, status):
    file = open("/proc/meminfo", 'r')
    line = file.readline().lstrip()
    count = 4
    while line:
        if line.startswith("MemTotal"):
            fields = line.split()
            status["os_mem_total"] = long(fields[1])*1024
            count -= 1
        elif line.startswith("MemFree"):
            fields = line.split()
            status["os_mem_free"] = long(fields[1])*1024
            count -= 1
        elif line.startswith("Buffers"):
            fields = line.split()
            status["os_mem_buffers"] = long(fields[1])*1024
            count -= 1
        elif line.startswith("Cached"):
            fields = line.split()
            status["os_mem_cached"] = long(fields[1])*1024
            count -= 1

        if count == 0:
            break;

        line = file.readline().lstrip()

    file.close()
    return

os_mem_section = StatusSection("os_mem", [
StatusColumn("total", 0, column_flags_bytes, field_handler_common, ["os_mem_total"],"Total memory size bytes."),
StatusColumn("free", 0, column_flags_bytes, field_handler_common, ["os_mem_free"],"Free memory size bytes."),
StatusColumn("buffer", 0, column_flags_bytes, field_handler_common, ["os_mem_buffers"],"Buffered memory size bytes."),
StatusColumn("cached", 0, column_flags_bytes, field_handler_common, ["os_mem_cached"],"Cached memory size bytes.")
], [get_os_mem_status],
"os memory status, collect from /proc/meminfo file")

proc_pid = 0
proc_pid_is_set = 0
def get_proc_cpu_status(server, status):
    global proc_pid_is_set
    global proc_pid
    if (proc_pid_is_set == 0):
        proc_pid_is_set = 1
        proc_pid = server.getPidNum(server)

    file = open("/proc/"+str(proc_pid)+"/stat", 'r')
    line = file.readline()
    file.close()

    fields = line.split()
    utime = long(fields[13])
    stime = long(fields[14])
    cutime = long(fields[15])
    cstime = long(fields[16])

    status["proc_cpu"] = utime + stime
    return

proc_cpu_section = StatusSection("proc_cpu", [
StatusColumn("%cpu", 0, column_flags_rate, field_handler_common, ["proc_cpu"], "Cpu utilization per second.")
], [get_proc_cpu_status],
"process cpu status, collect from /proc/[pid]/stat file, usually the pid should automatically "
"get from the server.getPidNum() function, but you can also replace the pid by the --proc-pid option")

def get_proc_mem_status(server, status):
    global proc_pid_is_set
    global proc_pid
    if (proc_pid_is_set == 0):
        proc_pid_is_set = 1
        proc_pid = server.getPidNum(server)

    file = open("/proc/"+str(proc_pid)+"/status", 'r')
    line = file.readline()

    count = 0
    while line:
        if (line.startswith("VmRSS")):
            fields = line.split()
            status["proc_mem_res"] = long(fields[1])*1024
            count += 1
        elif (line.startswith("VmSize")):
            fields = line.split()
            status["proc_mem_virt"] = long(fields[1])*1024
            count += 1

        if (count >= 2):
            break

        line = file.readline()

    file.close()
    return

proc_mem_section = StatusSection("proc_mem", [
StatusColumn("rss", 0, column_flags_bytes, field_handler_common, ["proc_mem_res"], "Bytes for resident memory size of the process in."),
StatusColumn("vsz", 0, column_flags_bytes, field_handler_common, ["proc_mem_virt"], "Bytes for virtual memory size of the process in.")
], [get_proc_mem_status],
"process memory status, collect from /proc/[pid]/status file, usually the pid should automatically "
"get from the server.getPidNum() function, but you can also replace the pid by the --proc-pid option")

common_sections = [
time_section,
os_cpu_section,
os_load_section,
os_swap_section,
os_net_bytes_section,
os_net_packages_section,
os_disk_section,
os_mem_section,
proc_cpu_section,
proc_mem_section
]

common_sections_to_show_default = [
time_section,
os_cpu_section,
os_disk_section,
os_net_bytes_section,
os_swap_section
]

####### Class Server #######
class Server:
    def __init__(self, name, type, initialize_func, clean_func, get_pidnum_func, sections):
        self.name = name
        self.type = type
        self.initialize = initialize_func   #initialize(server)
        self.clean = clean_func             #clean(server)
        self.getPidNumHandler = get_pidnum_func    #getPidNum(server)
        self.status_get_funcs = []
        self.sections = sections
        self.sections_to_show = []
        self.header_sections = ""
        self.header_columns = ""
        self.status = {}

    def getName(self):
        return self.name

    def getType(self):
        return self.type

    def getPidNum(self, server):
        if (self.getPidNumHandler == None):
            print "Please set the process pid number"
            sys.exit(3)

        return self.getPidNumHandler(server)

    def getSupportedSections(self):
        sections = []
        for section in common_sections:
            sections.append(section)

        for section in self.sections:
            sections.append(section)

        return sections

    def getSupportedSectionsName(self):
        sections = self.getSupportedSections()

        names = ""
        count = len(sections)
        for section in sections:
            name = section.getName()
            if (len(name) > 0):
                names += "'" + section.getName() + "'"
                if (count > 1):
                    names += ","

            count -= 1

        return names

    def isStatusGetFunctionAlreadyExist(self, function):
        for func in self.status_get_funcs:
            if (func[0] == function):
                return True

        return False

    def getStatusGetFunction(self, function):
        for func in self.status_get_funcs:
            if (func[0] == function):
                return func

        return None

    def addSectionStatusGetFunctions(self, section):
        added_count = 0
        for function in section.status_get_functions:
            func = self.getStatusGetFunction(function)
            if (func == None):
                self.status_get_funcs.append([function, 1])
                added_count += 1
            else:
                func[1] += 1

        return added_count

    def removeSectionStatusGetFunctions(self, section):
        removed_count = 0
        for function in section.status_get_functions:
            func = self.getStatusGetFunction(function)
            if (func != None):
                func[1] -= 1
                if (func[1] <= 0):
                    self.status_get_funcs.remove(func)
                    removed_count += 1

        return removed_count

    def setDefaultSectionsToShow(self, sections):
        self.sections_to_show = sections
        for section in sections:
            self.addSectionStatusGetFunctions(section)

        return

    def isSectionSupported(self, section_name):
        for section in common_sections:
            if (section_name == section.getName()):
                return True

        for section in self.sections:
            if (section_name == section.getName()):
                return True

        return False

    def getSectionByName(self, section_name):
        for section in common_sections:
            if (section_name == section.getName()):
                return section

        if (self.sections == None):
            return None

        for section in self.sections:
            if (section_name == section.getName()):
                return section

        return None

    def addSectionToShow(self, section_name):
        #Check if the section is already exsited.
        for section in self.sections_to_show:
            if (section.getName() == section_name):
                return 0

        section = self.getSectionByName(section_name)
        if (section == None):
            return -1

        self.sections_to_show.append(section)
        self.addSectionStatusGetFunctions(section)
        return 1

    def removeSectionFromShow(self, section_name):
        if (self.isSectionSupported(section_name) == False):
            return -1

        #Delete it if the section is exsited.
        for section in self.sections_to_show:
            if (section.getName() == section_name):
                self.sections_to_show.remove(section)
                self.removeSectionStatusGetFunctions(section)
                return 1

        return 0

    def getStatus(self):
        for func in self.status_get_funcs:
            func[0](self,self.status)

        return

    def showStatus(self):
        self.header_sections = get_sections_header(self.sections_to_show)
        self.header_columns = get_columns_header(self.sections_to_show)

        # Init the first status
        self.getStatus()
        get_status_line(self.sections_to_show, self.status)

        counter = 0
        while (1):
            time.sleep(interval)
            self.status.clear()

            if (separate_output_file_if_needed() == 1 or counter % 10 == 0):
                output(self.header_sections)
                output(self.header_columns)

            self.getStatus()
            output(get_status_line(self.sections_to_show, self.status))

            counter += 1

        return

####### Mysql Implement #######
def mysql_connection_create():
    import mysql.connector
    mysql_conn = mysql.connector.connect(
        user=user,
        password=password,
        host=host,
        port=port)
    return mysql_conn

def mysql_connection_destroy(conn):
    conn.close()
    return

def get_mysql_handler(conn):
    return conn.cursor()

def put_mysql_handler(handler):
    handler.close()
    return

def get_mysql_status(server, status):
    query= "show global status"
    server.cursor.execute(query)
    for (variable_name, value) in server.cursor:
        status[variable_name] = value
    return

def get_slave_status(server, status):
    query= "show slave status"
    server.cursor.execute(query)

    row = server.cursor.fetchone()
    if (row == None):
        status["seconds_behind_master"] = 0
        status["relay_log_space"] = 0
        return

    row_dict = dict(zip(server.cursor.column_names, row))
    status["seconds_behind_master"] = row_dict["Seconds_Behind_Master"]
    status["relay_log_space"] = row_dict["Relay_Log_Space"]

    return

def parse_innodb_status(innodb_status, status):
    for line in innodb_status.splitlines():
        if line.startswith("History list length"):
            fields = line.split()
            status["inno_history_list"] = fields[3]
        elif line.startswith("Log sequence number"):
            fields = line.split()
            if len(fields) == 5:
                status["redo_log_bytes_written"] = long(fields[3])*4294967296 + long(fields[4])
            else:
                status["redo_log_bytes_written"] = fields[3]
        elif line.startswith("Log flushed up to"):
            fields = line.split()
            if len(fields) == 6:
                status["redo_log_bytes_flushed"] = long(fields[4])*4294967296 + long(fields[5])
            else:
                status["redo_log_bytes_flushed"] = fields[4]
        elif line.startswith("Last checkpoint at"):
            fields = line.split()
            if len(fields) == 5:
                status["redo_log_last_checkpoint"] = long(fields[3])*4294967296 + long(fields[4])
            else:
                status["redo_log_last_checkpoint"] = fields[3]
        elif line.find("queries inside InnoDB") > 0:
            fields = line.split()
            status["inno_queries_inside"] = fields[0]
            status["inno_queries_queued"] = fields[4]
        elif line.find("read views open inside InnoDB") > 0:
            status["inno_read_views"] = line.split()[0]
        elif line.startswith("Mutex spin waits"):
            fields = line.split()
            status["inno_mutex_spin_waits"] = fields[3][0:-1]
            status["inno_mutex_rounds"] = fields[5][0:-1]
            status["inno_mutex_os_waits"] = fields[8]
        elif line.startswith("RW-shared spins"):
            fields = line.split()
            status["inno_shrdrw_spins"] = fields[2][0:-1]
            status["inno_shrdrw_rounds"] = fields[4][0:-1]
            status["inno_shrdrw_os_waits"] = fields[7]
        elif line.startswith("RW-excl spins"):
            fields = line.split()
            status["inno_exclrw_spins"] = fields[2][0:-1]
            status["inno_exclrw_rounds"] = fields[4][0:-1]
            status["inno_exclrw_os_waits"] = fields[7]

    return

def get_innodb_status(server, status):
    query= "show engine innodb status"
    server.cursor.execute(query)

    for (type, name, innodb_status) in server.cursor:
        parse_innodb_status(innodb_status, status)
        break

    return

def mysql_initialize_for_server(server):
    server.conn = mysql_connection_create()
    server.cursor = get_mysql_handler(server.conn)
    return

def mysql_clean_for_server(server):
    put_mysql_handler(server.cursor)
    mysql_connection_destroy(server.conn)
    return

def mysql_get_pidnum_for_server(server):
    query = "show global variables like 'pid_file'"
    server.cursor.execute(query)
    pid_file = ""
    for (variable_name, value) in server.cursor:
        pid_file = value
        break

    fd = open(pid_file, "r")
    pid = fd.read(20)
    fd.close()
    return int(pid)

def get_mysql_status_for_server(server):
    get_mysql_status(server.cursor, server.status)
    get_innodb_status(server.cursor, server.status)
    return

mysql_commands_section = StatusSection("cmds", [
StatusColumn("TPs", 0, column_flags_rate, field_handler_common, ["Com_commit", "Com_rollback"], "Transactions per second."),
StatusColumn("QPs", 0, column_flags_rate, field_handler_common, ["Com_select"], "Select commands per second."),
StatusColumn("DPs", 0, column_flags_rate, field_handler_common,["Com_delete"], "Delete commands per second."),
StatusColumn("IPs", 0, column_flags_rate, field_handler_common,["Com_insert"], "Insert commands per second."),
StatusColumn("UPs", 0, column_flags_rate, field_handler_common,["Com_update"], "Update commands per second."),
StatusColumn("DIUPs", 0, column_flags_rate, field_handler_common,["Com_delete","Com_insert","Com_update"], "DDL(delete+insert+update) commands per second.")
], [get_mysql_status],
"mysql commands status, collect from \'show global status\'")

mysql_net_section = StatusSection("net", [
StatusColumn("NetIn", 0, column_flags_rate|column_flags_bytes, field_handler_common,["Bytes_received"], "Bytes per second received from all clients."),
StatusColumn("NetOut", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["Bytes_sent"], "Bytes per second sent to all clients.")
], [get_mysql_status],
"mysql network status, collect from \'show global status\'")

mysql_threads_section = StatusSection("threads_conns", [
StatusColumn("Run", 0, column_flags_none, field_handler_common, ["Threads_running"], "The number of threads that are not sleeping."),
StatusColumn("Create", 0, column_flags_rate, field_handler_common, ["Threads_created"], "Counts per second of threads created to handle connections."),
StatusColumn("Cache", 0, column_flags_none, field_handler_common, ["Threads_cached"], "The number of threads in the thread cache."),
StatusColumn("Conns", 0, column_flags_none, field_handler_common, ["Threads_connected"], "The number of currently open connections."),
StatusColumn("Try", 0, column_flags_rate, field_handler_common, ["Connections"], "Counts per second of connection attempts (successful or not) to the MySQL server."),
StatusColumn("Abort", 0, column_flags_rate, field_handler_common, ["Aborted_connects"], "Counts per second of failed attempts to connect to the MySQL server.")
], [get_mysql_status],
"mysql thread status, collect from \'show global status\'")

mysql_innodb_redo_log_section = StatusSection("innodb_redo_log", [
StatusColumn("Written", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["redo_log_bytes_written"], "Bytes per second redo log data written."),
StatusColumn("Flushed", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["redo_log_bytes_flushed"], "Bytes per second redo log data flushed."),
StatusColumn("Checked", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["redo_log_last_checkpoint"], "Bytes per second redo log data checked.")
], [get_innodb_status],
"mysql innodb redo log status, collect from \'show engine innodb status\'")

mysql_innodb_log_section = StatusSection("innodb_log", [
StatusColumn("HisList", 0, column_flags_none, field_handler_common, ["inno_history_list"], "History list length."),
StatusColumn("Fsyncs", 0, column_flags_rate, field_handler_common, ["Innodb_os_log_fsyncs"], "Counts per second of fsync() writes done to the log file."),
StatusColumn("Written", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["Innodb_os_log_written"], "Bytes per second written to the log file.")
], [get_mysql_status, get_innodb_status],
"mysql innodb redo log status, collect from \'show global status\' and \'show engine innodb status\'")

mysql_innodb_buffer_pool_usage_section = StatusSection("innodb_bp_usage", [
StatusColumn("DataPct", 0, column_flags_ratio, field_handler_common, ["Innodb_buffer_pool_pages_data","Innodb_buffer_pool_pages_total"], "Data pages percentage of possession in total pages."),
StatusColumn("Dirty", 0, column_flags_none, field_handler_common, ["Innodb_buffer_pool_pages_dirty"], "The number of pages currently dirty."),
StatusColumn("DReads", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_reads"], "Counts per second of logical reads that InnoDB could not satisfy from the buffer pool, and had to read directly from the disk."),
StatusColumn("Reads", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_read_requests"], "Counts per second of logical read requests."),
StatusColumn("Writes", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_write_requests"], "Counts per second of writes done to the InnoDB buffer pool.")
], [get_mysql_status],
"mysql innodb buffer pool status, collect from \'show global status\'")

mysql_innodb_rows_section = StatusSection("innodb_rows", [
StatusColumn("Insert", 0, column_flags_rate, field_handler_common, ["Innodb_rows_inserted"], "Counts per second of rows inserted into InnoDB tables."),
StatusColumn("Update", 0, column_flags_rate, field_handler_common, ["Innodb_rows_updated"], "Counts per second of rows updated in InnoDB tables."),
StatusColumn("Delete", 0, column_flags_rate, field_handler_common, ["Innodb_rows_deleted"], "Counts per second of rows deleted in InnoDB tables."),
StatusColumn("Read", 0, column_flags_rate, field_handler_common, ["Innodb_rows_read"], "Counts per second of rows read from InnoDB tables.")
], [get_mysql_status],
"mysql innodb rows status, collect from \'show global status\'")

mysql_innodb_data_section = StatusSection("innodb_data", [
StatusColumn("Reads", 0, column_flags_rate, field_handler_common, ["Innodb_data_reads"], "Counts per second of data reads (OS file reads)."),
StatusColumn("Writes", 0, column_flags_rate, field_handler_common, ["Innodb_data_writes"], "Counts per second of data writes."),
StatusColumn("Read", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["Innodb_data_read"], "Bytes per second data read."),
StatusColumn("Written", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["Innodb_data_written"], "Bytes per second data written.")
], [get_mysql_status],
"mysql innodb data status, collect from \'show global status\'")

mysql_innodb_row_lock_section = StatusSection("row_lock", [
StatusColumn("LWaits", 0, column_flags_rate, field_handler_common, ["Innodb_row_lock_waits"], "Times per second "
    "a row lock had to be waited for."),
StatusColumn("LTime", 0, column_flags_rate, field_handler_common, ["Innodb_row_lock_time"], "Milliseconds spent "
    "in acquiring row locks among one second.")
], [get_mysql_status],
"mysql row lock status, collect from \'show global status\'")

mysql_table_lock_section = StatusSection("table_lock", [
StatusColumn("LWait", 0, column_flags_rate, field_handler_common, ["Table_locks_waited"], "Times per second that "
    "a request for a table lock could not be granted immediately and a wait was needed. If this is high "
    "and you have performance problems, you should first optimize your queries, and then either split "
    "your table or tables or use replication."),
StatusColumn("LImt", 0, column_flags_rate, field_handler_common, ["Table_locks_immediate"], "Times per second "
    "that a request for a table lock could be granted immediately.")
], [get_mysql_status],
"mysql table lock status, collect from \'show global status\'")

mysql_innodb_internal_lock_section = StatusSection("innodb_internal_lock", [
StatusColumn("MSpin", 0, column_flags_rate, field_handler_common, ["inno_mutex_spin_waits"], "Times per second "
    "the Mutex spin waits."),
StatusColumn("MRound", 0, column_flags_rate, field_handler_common, ["inno_mutex_rounds"], "Times per second the "
    "threads looped in the spin-wait cycle for Mutex."),
StatusColumn("MOWait", 0, column_flags_rate, field_handler_common, ["inno_mutex_os_waits"], "Times per second "
    "the thread gave up spin-waiting and went to sleep instead for Mutex."),
StatusColumn("SSpin", 0, column_flags_rate, field_handler_common, ["inno_shrdrw_spins"], "Times per second the "
    "RW-shared spin waits."),
StatusColumn("SRound", 0, column_flags_rate, field_handler_common, ["inno_shrdrw_rounds"], "Times per second "
    "the threads looped in the spin-wait cycle for RW-shared."),
StatusColumn("SOWait", 0, column_flags_rate, field_handler_common, ["inno_shrdrw_os_waits"], "Times per second "
    "the thread gave up spin-waiting and went to sleep instead for RW-shared."),
StatusColumn("ESpin", 0, column_flags_rate, field_handler_common, ["inno_exclrw_spins"], "Times per second the "
    "RW-excl spin waits."),
StatusColumn("ERound", 0, column_flags_rate, field_handler_common, ["inno_exclrw_rounds"], "Times per second "
    "the threads looped in the spin-wait cycle for RW-excl."),
StatusColumn("EOWait", 0, column_flags_rate, field_handler_common, ["inno_exclrw_os_waits"], "Times per second "
    "the thread gave up spin-waiting and went to sleep instead for RW-excl.")
], [get_innodb_status],
"mysql innodb internal lock status, collect from \'show engine innodb status\'")

mysql_slave_section = StatusSection("slave", [
StatusColumn("Delay", 0, column_flags_none, field_handler_common, ["seconds_behind_master"], "This is the \'Seconds_Behind_Master\', "
    "based on the timestamps stored in events, measures the time difference in seconds between the slave SQL thread and the "
    "slave I/O thread. If the network connection between master and slave is fast, the slave I/O thread is very close to "
    "the master, so this field is a good approximation of how late the slave SQL thread is compared to the master. "
    "If the network is slow, this is not a good approximation; the slave SQL thread may quite often be caught up with "
    "the slow-reading slave I/O thread, so Seconds_Behind_Master often shows a value of 0, even if the I/O thread is "
    "late compared to the master. In other words, this column is useful only for fast networks."),
StatusColumn("RSpace", 0, column_flags_bytes, field_handler_common, ["relay_log_space"], "The total combined size of all existing relay log files.")
], [get_slave_status],
"mysql slave status, collect from \'show slave status\'")

mysql_handler_read_section = StatusSection("handler_read", [
StatusColumn("First", 0, column_flags_rate, field_handler_common, ["Handler_read_first"], "Times per second the first entry in an index was read. If this value is high, it suggests that the server is doing a lot of full index scans; for example, SELECT col1 FROM foo, assuming that col1 is indexed."),
StatusColumn("Key", 0, column_flags_rate, field_handler_common, ["Handler_read_key"], "Requests per second to read a row based on a key. If this value is high, it is a good indication that your tables are properly indexed for your queries."),
StatusColumn("Last", 0, column_flags_rate, field_handler_common, ["Handler_read_last"], "Requests per second to read the last key in an index. With ORDER BY, the server will issue a first-key request followed by several next-key requests, whereas with ORDER BY DESC, the server will issue a last-key request followed by several previous-key requests. This variable was added in MySQL 5.5.7."),
StatusColumn("Next", 0, column_flags_rate, field_handler_common, ["Handler_read_next"], "Requests per second to read the next row in key order. This value is incremented if you are querying an index column with a range constraint or if you are doing an index scan."),
StatusColumn("Prev", 0, column_flags_rate, field_handler_common, ["Handler_read_prev"], "Requests per second to read the previous row in key order. This read method is mainly used to optimize ORDER BY ... DESC."),
StatusColumn("Rnd", 0, column_flags_rate, field_handler_common, ["Handler_read_rnd"], "Requests per second to read a row based on a fixed position. This value is high if you are doing a lot of queries that require sorting of the result. You probably have a lot of queries that require MySQL to scan entire tables or you have joins that do not use keys properly."),
StatusColumn("RNext", 0, column_flags_rate, field_handler_common, ["Handler_read_rnd_next"], "Requests per second to read the next row in the data file. This value is high if you are doing a lot of table scans. Generally this suggests that your tables are not properly indexed or that your queries are not written to take advantage of the indexes you have.")
], [get_mysql_status],
"mysql handler read status, collect from \'show global status\' about \'Handler_read_*\' variables")

mysql_handler_ddl_section = StatusSection("handler_ddl", [
StatusColumn("Write", 0, column_flags_rate, field_handler_common, ["Handler_write"], "Requests per second to insert a row in a table."),
StatusColumn("Update", 0, column_flags_rate, field_handler_common, ["Handler_update"], "Requests per second to update a row in a table."),
StatusColumn("Del", 0, column_flags_rate, field_handler_common, ["Handler_delete"], "Times per second that rows have been deleted from tables")
], [get_mysql_status],
"mysql handler ddl status, collect from \'show global status\'")

mysql_handler_transaction_section = StatusSection("handler_trx", [
StatusColumn("Commit", 0, column_flags_rate, field_handler_common, ["Handler_commit"], "Counts per second of internal COMMIT statements."),
StatusColumn("Pre", 0, column_flags_rate, field_handler_common, ["Handler_prepare"], "Counts per second of the prepare phase of two-phase commit operations."),
StatusColumn("Rback", 0, column_flags_rate, field_handler_common, ["Handler_rollback"], "Requests per second for a storage engine to perform a rollback operation."),
StatusColumn("Spoint", 0, column_flags_rate, field_handler_common, ["Handler_savepoint"], "Requests per second for a storage engine to place a savepoint."),
StatusColumn("SPRb", 0, column_flags_rate, field_handler_common, ["Handler_savepoint_rollback"], "Requests per second for a storage engine to roll back to a savepoint."),
], [get_mysql_status],
"mysql handler transaction status, collect from \'show global status\'")

mysql_sections = [
mysql_commands_section,
mysql_net_section,
mysql_threads_section,
mysql_innodb_redo_log_section,
mysql_innodb_log_section,
mysql_innodb_buffer_pool_usage_section,
mysql_innodb_rows_section,
mysql_innodb_data_section,
mysql_innodb_row_lock_section,
mysql_table_lock_section,
mysql_innodb_internal_lock_section,
mysql_slave_section,
mysql_handler_read_section,
mysql_handler_ddl_section,
mysql_handler_transaction_section
]
mysql_sections_to_show_default = [
time_section,
mysql_commands_section,
mysql_net_section,
mysql_threads_section
]

####### Redis Implement #######
def redis_connection_create():
    import redis.connection
    redis_conn = redis.StrictRedis(
        host=host,
        port=port,
        password=password)
    return redis_conn

def redis_connection_destroy(conn):
    return

def redis_initialize_for_server(server):
    server.redis_conn = redis_connection_create()
    return

def redis_clean_for_server(server):
    redis_connection_destroy(server.redis_conn)
    return

def redis_get_pidnum_for_server(server):
    pid = server.redis_conn.info("server")["process_id"]
    return int(pid)

def get_redis_status(server, status):
    redis_info = server.redis_conn.info()
    for key in redis_info:
        status[key] = redis_info[key]
    return

def field_handler_redis_keyspace(column, status):
    keys_count = 0
    expires_count = 0
    for idx in range(10000):
        if (status.has_key("db"+str(idx)) == False):
            break;

        db_message = status["db"+str(idx)]
        keys_count += long(db_message["keys"])
        expires_count += long(db_message["expires"])

    if (column.getName() == "keys"):
        return num2readable(keys_count)
    elif (column.getName() == "expires"):
        return num2readable(expires_count)

    return "0"

redis_client_section = StatusSection("client", [
StatusColumn("Conns", 0, column_flags_none, field_handler_common, ["connected_clients"], "Counts for connected clients."),
StatusColumn("LOList", 0, column_flags_none, field_handler_common, ["client_longest_output_list"], "Longest client output list length."),
StatusColumn("BIBuf", 0, column_flags_bytes, field_handler_common, ["client_biggest_input_buf"], "Biggest client input buffer size in bytes.")
], [get_redis_status],
"redis client status, collect from \'info\'")

redis_memory_section = StatusSection("mem", [
StatusColumn("used", 0, column_flags_bytes, field_handler_common, ["used_memory"], "Total number of bytes allocated by Redis using its allocator (either standard libc, jemalloc, or an alternative allocator such as tcmalloc."),
StatusColumn("rss", 0, column_flags_bytes, field_handler_common, ["used_memory_rss"], "Number of bytes that Redis allocated as seen by the operating system (a.k.a resident set size). This is the number reported by tools such as top(1) and ps(1)."),
StatusColumn("peak", 0, column_flags_bytes, field_handler_common, ["used_memory_peak"], "Peak memory consumed by Redis (in bytes).")
], [get_redis_status],
"redis memory usage, collect from \'info\'")

redis_net_section = StatusSection("net", [
StatusColumn("in", 0, column_flags_bytes|column_flags_rate, field_handler_common, ["total_net_input_bytes"], "Bytes per second received into redis."),
StatusColumn("out", 0, column_flags_bytes|column_flags_rate, field_handler_common, ["total_net_output_bytes"], "Bytes per second sent by redis.")
], [get_redis_status],
"redis network status, collect from \'info\'")

redis_keyspace_section = StatusSection("keyspace", [
StatusColumn("keys", 0, column_flags_none, field_handler_redis_keyspace, [], "Number of keys in all db."),
StatusColumn("expires", 0, column_flags_none, field_handler_redis_keyspace, [], "Number of keys with an expiration in all db.")
], [get_redis_status],
"redis keyspace status, collect from \'info\'")

redis_sections = [
redis_client_section,
redis_memory_section,
redis_net_section,
redis_keyspace_section
]

redis_sections_to_show_default = [
time_section,
proc_cpu_section,
redis_memory_section,
redis_net_section,
redis_client_section,
redis_keyspace_section
]

####### sss #######
def usage():
    print 'python sss.py [options]'
    print ''
    print 'options:'
    print '-h,--help: show this help message'
    print '-v,--version: show the version'
    print '-H: target host'
    print '-P: target port'
    print '-u: target service user'
    print '-p: target user password'
    print '-T: target service type, default is os'
    print '-s: sections to show, use comma to split'
    print '-a: addition sections to show, use comma to split'
    print '-d: removed sections for the showing, use comma to split'
    print '-I,--instructions: show the support sections\' instructions'
    print '-o: output the status to this file'
    print '-D: separate output files by day, suffix of the file name is \'_yyyy-mm-dd\''
    print '-i: interval time to show the status, unit is second'
    print '--net-face: set the net device face name for os_net_* sections, default is \'lo\''
    print '--disk-name: set the disk device name for os_disk sections, default is \'vda\''
    print '--proc-pid: set the process pid number for proc_* sections, default is 0'

def version():
    return '0.1.1'

def print_version():
    print "sss version " + version()
    return

def print_sections_instructions(server):
    segmentation_line = "_"*segmentation_line_len
    sections = server.getSupportedSections()
    print_version()
    print "* Use -T option to set the service type and show the type support sections\' instructions"
    print ""
    print server.getName() + " status sections\' instructions are as follows"
    print segmentation_line
    for section in sections:
        print get_section_instructions(section)
        print segmentation_line

    return

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvIH:P:u:p:T:s:a:d:o:Di:', ['help', 'version', 'instructions', 'net-face=', 'disk-name=', 'proc-pid='])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    instructions_show = 0
    all_section = 0
    sections_name = []
    sections_name_addition = []
    sections_name_removed = []
    for opt, arg in opts:
        if opt in ('-h','--help'):
            usage()
            sys.exit(1)
        elif opt in ('-v','--version'):
            print_version()
            sys.exit(1)
        elif opt in ('-I','--instructions'):
            instructions_show = 1
        elif opt in ('-H'):
            host = arg
        elif opt in ('-P'):
            port = int(arg)
        elif opt in ('-u'):
            user = arg
        elif opt in ('-p'):
            password = arg
        elif opt in ('-T'):
            service_type = arg
            find = 0
            for elem in support_types:
                if (service_type == elem):
                    find = 1
                    break

            if (find == 0):
                print service_type + " is not support type"
                print "Support types: " + getSupportedServiceTypesName()
                sys.exit(3)
        elif opt in ('-s'):
            if (arg == 'all'):
                all_section = 1
            else:
                sections_name = arg.split(',')
        elif opt in ('-a'):
            sections_name_addition = arg.split(',')
        elif opt in ('-d'):
            sections_name_removed = arg.split(',')
        elif opt in ('-o'):
            output_type = 1
            output_file_name = arg
        elif opt in ('-D'):
            output_file_by_day = 1
        elif opt in ('-i'):
            interval = int(arg)
        elif opt in ('--net-face'):
            net_face_name = arg
        elif opt in ('--disk-name'):
            disk_name = arg
        elif opt in ('--proc-pid'):
            proc_pid = int(arg)
            proc_pid_is_set = 1
        else:
            print 'Unhandled option'
            sys.exit(3)

    server = None
    if (service_type == type_os):
        server = Server("OS", service_type, None, None, None, [])
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
        else:
            server.setDefaultSectionsToShow(common_sections_to_show_default)
    elif (service_type == type_mysql):
        server = Server("Mysql", service_type,
                        mysql_initialize_for_server,
                        mysql_clean_for_server,
                        mysql_get_pidnum_for_server,
                        mysql_sections)
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
            for section in mysql_sections:
                server.addSectionToShow(section.getName())
        elif (len(sections_name) == 0):
            server.setDefaultSectionsToShow(mysql_sections_to_show_default)
    elif (service_type == type_redis):
        server = Server("Redis", service_type,
                        redis_initialize_for_server,
                        redis_clean_for_server,
                        redis_get_pidnum_for_server,
                        redis_sections)
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
            for section in redis_sections:
                server.addSectionToShow(section.getName())
        elif (len(sections_name) == 0):
            server.setDefaultSectionsToShow(redis_sections_to_show_default)

    if (instructions_show == 1):
        print_sections_instructions(server)
        sys.exit(1)

    for section_name in sections_name:
        if all_section == 1:
            break

        ret = server.addSectionToShow(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getType())
            print server.getType() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    for section_name in sections_name_addition:
        ret = server.addSectionToShow(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getType())
            print server.getType() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    for section_name in sections_name_removed:
        ret = server.removeSectionFromShow(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getType())
            print server.getType() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    if (output_type == 1):
        output_file = open(output_file_name+'_'+current_day, 'a', 0)

    # Init the server if needed.
    if (server.initialize != None):
        server.initialize(server)

    server.showStatus()

    # Clean the server if needed.
    if (server.clean != None):
        server.clean(server)

    if (output_type == 1 and output_file.closed == False):
        output_file.close()