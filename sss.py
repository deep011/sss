#!/usr/bin/python

import time
import getopt
import sys

import mysql.connector

type_mysql = "mysql"
support_types=[type_mysql]

type=type_mysql

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

####### Util #######
def byte2readable(bytes):
    bytes_float = float(bytes)
    if bytes_float > -1024.0 and bytes_float < 1024.0:
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
        return str(number)
    else:
        number_float /= 1000.0
    for count in ['k', 'm', 'g']:
        if number_float > -1000.0 and number_float < 1000.0:
            return "%3.1f%s" % (number_float, count)

        number_float /= 1000.0
    return "%3.1f%s" % (number_float, 't')

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
    def __init__(self, name, columns, status_get_functions):
        self.name = name
        self.columns = columns
        self.status_get_functions = status_get_functions

    def getName(self):
        return self.name
    def getColumns(self):
        return self.columns

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
    def __init__(self, name, blanks, flags, field_handler, fields):
        self.name = name
        self.width = 15
        self.flags = flags
        self.field_handler = field_handler
        self.fields = fields
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

def field_handler_time(column, status):
    return column_format % (9, time.strftime("%H:%M:%S", time.localtime()))

time_section = StatusSection("time", [
StatusColumn("Time", 5, column_flags_string, field_handler_time, [])
],[])

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
StatusColumn("usr", 2, column_flags_rate, field_handler_os_cpu, ["os_cpu_usr","os_cpu_total"]),
StatusColumn("sys", 2, column_flags_rate, field_handler_os_cpu, ["os_cpu_sys","os_cpu_total"]),
StatusColumn("idl", 2, column_flags_rate, field_handler_os_cpu, ["os_cpu_idl","os_cpu_total"]),
StatusColumn("iow", 2, column_flags_rate, field_handler_os_cpu, ["os_cpu_iow","os_cpu_total"])
],[get_os_cpu_status])

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
StatusColumn("1m", 4, column_flags_string, field_handler_common, ["os_load_one"]),
StatusColumn("5m", 4, column_flags_string, field_handler_common, ["os_load_five"]),
StatusColumn("15m", 3, column_flags_string, field_handler_common, ["os_load_fifteen"])
],[get_os_load_status])

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
StatusColumn("si", 4, column_flags_rate, field_handler_common, ["os_swap_pswpin"]),
StatusColumn("so", 4, column_flags_rate, field_handler_common, ["os_swap_pswpout"])
],[get_os_swap_status])

common_sections = [
time_section,
os_cpu_section,
os_load_section,
os_swap_section
]

####### Class Server #######
class Server:
    def __init__(self, name, type, initialize_func, clean_func, sections):
        self.name = name
        self.type = type
        self.initialize = initialize_func   #initialize(server)
        self.clean = clean_func             #clean(server)
        self.status_get_funcs = []
        self.sections = sections
        self.sections_to_show = []
        self.header_sections = ""
        self.header_columns = ""
        self.status = {}

    def getName(self):
        return self.name

    def getSupportedSectionsName(self):
        names = ""
        count = len(common_sections) + len(self.sections)
        for section in common_sections:
            name = section.getName()
            if (len(name) > 0):
                names += "'" + section.getName() + "'"
                if (count > 1):
                    names += ","

            count -= 1

        for section in self.sections:
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

def get_mysql_pid(cursor):
    query = "show global variables like 'pid_file'"
    cursor.execute(query)
    for (variable_name, value) in cursor:
        pid_file = value
        break
    fd = open(pid_file, "r")
    pid = fd.read(20)
    fd.close()
    return int(pid)

def get_mysql_status(server, status):
    query= "show global status"
    server.cursor.execute(query)
    for (variable_name, value) in server.cursor:
        status[variable_name] = value
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

def get_innodb_status(cursor, status):
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

def get_mysql_status_for_server(server):
    get_mysql_status(server.cursor, server.status)
    get_innodb_status(server.cursor, server.status)
    return

mysql_commands_section = StatusSection("cmds", [
StatusColumn("TPs", 0, column_flags_rate, field_handler_common, ["Com_commit", "Com_rollback"]),
StatusColumn("QPs", 0, column_flags_rate, field_handler_common, ["Com_select"]),
StatusColumn("DPs", 0, column_flags_rate, field_handler_common,["Com_delete"]),
StatusColumn("IPs", 0, column_flags_rate, field_handler_common,["Com_insert"]),
StatusColumn("UPs", 0, column_flags_rate, field_handler_common,["Com_update"]),
StatusColumn("DIUPs", 0, column_flags_rate, field_handler_common,["Com_delete","Com_insert","Com_update"])
], [get_mysql_status])

mysql_net_section = StatusSection("net", [
StatusColumn("NetIn", 0, column_flags_rate|column_flags_bytes, field_handler_common,["Bytes_received"]),
StatusColumn("NetOut", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["Bytes_sent"])
], [get_mysql_status])

mysql_threads_section = StatusSection("threads_conns", [
StatusColumn("Run", 0, column_flags_none, field_handler_common, ["Threads_running"]),
StatusColumn("Create", 0, column_flags_rate, field_handler_common, ["Threads_created"]),
StatusColumn("Cache", 0, column_flags_none, field_handler_common, ["Threads_cached"]),
StatusColumn("Conns", 0, column_flags_none, field_handler_common, ["Threads_connected"]),
StatusColumn("Try", 0, column_flags_rate, field_handler_common, ["Connections"]),
StatusColumn("Abort", 0, column_flags_rate, field_handler_common, ["Aborted_connects"])
], [get_mysql_status])

mysql_innodb_redo_log_section = StatusSection("innodb_redo_log", [
StatusColumn("Written", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["redo_log_bytes_written"]),
StatusColumn("Flushed", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["redo_log_bytes_flushed"]),
StatusColumn("Checked", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["redo_log_last_checkpoint"])
], [get_innodb_status])

mysql_innodb_log_section = StatusSection("innodb_log", [
StatusColumn("HisList", 0, column_flags_none, field_handler_common, ["inno_history_list"]),
StatusColumn("Fsyncs", 0, column_flags_rate, field_handler_common, ["Innodb_os_log_fsyncs"]),
StatusColumn("Written", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["Innodb_os_log_written"])
], [get_mysql_status, get_innodb_status])

mysql_innodb_buffer_pool_usage_section = StatusSection("innodb_bp_usage", [
StatusColumn("DataPct", 0, column_flags_ratio, field_handler_common, ["Innodb_buffer_pool_pages_data","Innodb_buffer_pool_pages_total"]),
StatusColumn("Dirty", 0, column_flags_none, field_handler_common, ["Innodb_buffer_pool_pages_dirty"]),
StatusColumn("MReads", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_reads"]),
StatusColumn("Reads", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_read_requests"]),
StatusColumn("Writes", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_write_requests"])
], [get_mysql_status])

mysql_innodb_rows_section = StatusSection("innodb_rows", [
StatusColumn("Insert", 0, column_flags_rate, field_handler_common, ["Innodb_rows_inserted"]),
StatusColumn("Update", 0, column_flags_rate, field_handler_common, ["Innodb_rows_updated"]),
StatusColumn("Delete", 0, column_flags_rate, field_handler_common, ["Innodb_rows_deleted"]),
StatusColumn("Read", 0, column_flags_rate, field_handler_common, ["Innodb_rows_read"])
], [get_mysql_status])

mysql_innodb_data_section = StatusSection("innodb_data", [
StatusColumn("Reads", 0, column_flags_rate, field_handler_common, ["Innodb_data_reads"]),
StatusColumn("Writes", 0, column_flags_rate, field_handler_common, ["Innodb_data_writes"]),
StatusColumn("Read", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["Innodb_data_read"]),
StatusColumn("Written", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["Innodb_data_written"])
], [get_mysql_status])

mysql_innodb_row_lock_section = StatusSection("row_lock", [
StatusColumn("LWaits", 0, column_flags_rate, field_handler_common, ["Innodb_row_lock_waits"]),
StatusColumn("LTime", 0, column_flags_rate, field_handler_common, ["Innodb_row_lock_time"])
], [get_mysql_status])

mysql_table_lock_section = StatusSection("table_lock", [
StatusColumn("LWait", 0, column_flags_rate, field_handler_common, ["Table_locks_waited"]),
StatusColumn("LImt", 0, column_flags_rate, field_handler_common, ["Table_locks_immediate"])
], [get_mysql_status])

mysql_innodb_internal_lock_section = StatusSection("innodb_internal_lock", [
StatusColumn("MSpin", 0, column_flags_rate, field_handler_common, ["inno_mutex_spin_waits"]),
StatusColumn("MRound", 0, column_flags_rate, field_handler_common, ["inno_mutex_rounds"]),
StatusColumn("MOWait", 0, column_flags_rate, field_handler_common, ["inno_mutex_os_waits"]),
StatusColumn("SSpin", 0, column_flags_rate, field_handler_common, ["inno_shrdrw_spins"]),
StatusColumn("SRound", 0, column_flags_rate, field_handler_common, ["inno_shrdrw_rounds"]),
StatusColumn("SOWait", 0, column_flags_rate, field_handler_common, ["inno_shrdrw_os_waits"]),
StatusColumn("ESpin", 0, column_flags_rate, field_handler_common, ["inno_exclrw_spins"]),
StatusColumn("ERound", 0, column_flags_rate, field_handler_common, ["inno_exclrw_rounds"]),
StatusColumn("EOWait", 0, column_flags_rate, field_handler_common, ["inno_exclrw_os_waits"])
], [get_innodb_status])

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
mysql_innodb_internal_lock_section
]
mysql_sections_to_show_default = [
time_section,
mysql_commands_section,
mysql_net_section,
mysql_threads_section
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
    print '-T: target service type, default is mysql'
    print '-s: sections to show, use comma to split'
    print '-a: addition sections to show, use comma to split'
    print '-d: removed sections for the showing, use comma to split'
    print '-o: output the status to this file'
    print '-D: separate output files by day, suffix of the file name is \'_yyyy-mm-dd\''
    print '-i: interval time to show the status, unit is second'

def version():
    return '0.1.0'

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvH:P:u:p:T:s:a:d:o:Di:', ['help', 'version'])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    all_section = 0
    sections_name = []
    sections_name_addition = []
    sections_name_removed = []
    for opt, arg in opts:
        if opt in ('-h','--help'):
            usage()
            sys.exit(1)
        elif opt in ('-v','--version'):
            print version()
            sys.exit(1)
        elif opt in ('-H'):
            host = arg
        elif opt in ('-P'):
            port = int(arg)
        elif opt in ('-u'):
            user = arg
        elif opt in ('-p'):
            password = arg
        elif opt in ('-T'):
            type = arg
            find = 0
            for elem in support_types:
                if (type == elem):
                    find = 1
                    break

            if (find == 0):
                print "Unsupport type"
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
        else:
            print 'Unhandled option'
            sys.exit(3)

    server = None
    if (type == type_mysql):
        server = Server("Mysql", type,
                        mysql_initialize_for_server,
                        mysql_clean_for_server,
                        mysql_sections)
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
            for section in mysql_sections:
                server.addSectionToShow(section.getName())
        elif (len(sections_name) == 0):
            server.setDefaultSectionsToShow(mysql_sections_to_show_default)

    for section_name in sections_name:
        if all_section == 1:
            break

        ret = server.addSectionToShow(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getName())
            print server.getName() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    for section_name in sections_name_addition:
        ret = server.addSectionToShow(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getName())
            print server.getName() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    for section_name in sections_name_removed:
        ret = server.removeSectionFromShow(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getName())
            print server.getName() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    if (output_type == 1):
        output_file = open(output_file_name+'_'+current_day, 'a', 0)

    server.initialize(server)
    server.showStatus()
    server.clean(server)

    if (output_type == 1 and output_file.closed == False):
        output_file.close()