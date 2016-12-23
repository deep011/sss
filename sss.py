#!/usr/bin/python

import time
import mysql.connector
import getopt
import sys

type_mysql = "mysql"
support_types=[type_mysql]

type=type_mysql

host="127.0.0.1"
port=3306
user="root"
password=""

interval=1 #second

#column_format = '%-*s'
column_format = '%*s'

####### Util #######
def byte2readable(bytes):
    bytes = float(bytes)
    if bytes > -1024.0 and bytes < 1024.0:
        return str(bytes)
    else:
        bytes /= 1024.0
    for count in ['K', 'M', 'G']:
        if bytes > -1024.0 and bytes < 1024.0:
            return "%3.1f%s" % (bytes, count)
        bytes /= 1024.0
    return "%3.1f%s" % (bytes, 'T')

####### Show #######
class StatusSection:
    def __init__(self, name, columns):
        self.name = name
        self.columns = columns

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
        if (blanks <= 2):  # Blanks is zero means the default blanks count between the columns, default is 2.
            self.width = len(name)+2
        elif (blanks > 0):
            self.width = len(name) + blanks

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

    def getHeader(self):
        return column_format % (self.getWidth(), self.getName())

    def getValue(self, column, status):
        return column.field_handler(column, status)

    def setValueOld(self, value):
        self.value_old = value

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
        value_str = str(rate)
    else:
        if (column.getFlags()&column_flags_string == 0):
            value_str = str(value_num)

    if (column.getFlags() & column_flags_bytes):
        return byte2readable(value_str)

    return value_str

def get_status_line(sections, status):
    line = ""
    for section in sections:
        for column in section.getColumns():
            line += column_format % (column.getWidth(), column.getValue(column, status))
        line += '|'
    return line

####### Common #######
def field_handler_time(column, status):
    return column_format % (9, time.strftime("%H:%M:%S", time.localtime()))

time_section = StatusSection("time", [
StatusColumn("Time", 5, column_flags_string, field_handler_time, [])
])

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

common_sections = [
time_section
]

def get_supported_sections_name(sections):
    names = ""
    count = len(common_sections) + len(sections)
    for section in common_sections:
        name = section.getName()
        if (len(name) > 0):
            names += "'" + section.getName() + "'"
            if (count > 1):
                names += ","

        count -= 1
    for section in sections:
        name = section.getName()
        if (len(name) > 0):
            names += "'" + section.getName() + "'"
            if (count > 1):
                names += ","

        count -= 1

    return names

####### Mysql #######
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

def get_mysql_status(cursor, status):
    query= "show global status"
    cursor.execute(query)
    for (variable_name, value) in cursor:
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
                status["inno_log_bytes_written"] = long(fields[3])*4294967296 + long(fields[4])
            else:
                status["inno_log_bytes_written"] = fields[3]
        elif line.startswith("Log flushed up to"):
            fields = line.split()
            if len(fields) == 6:
                status["inno_log_bytes_flushed"] = long(fields[4])*4294967296 + long(fields[5])
            else:
                status["inno_log_bytes_flushed"] = fields[4]
        elif line.startswith("Last checkpoint at"):
            fields = line.split()
            if len(fields) == 5:
                status["inno_last_checkpoint"] = long(fields[3])*4294967296 + long(fields[4])
            else:
                status["inno_last_checkpoint"] = fields[3]
        elif line.find("queries inside InnoDB") > 0:
            fields = line.split()
            status["inno_queries_inside"] = fields[0]
            status["inno_queries_queued"] = fields[4]
        elif line.find("read views open inside InnoDB") > 0:
            status["inno_read_views"] = line.split()[0]
        elif line.startswith("Mutex spin waits"):
            fields = line.split()
            status["inno_mutex_spin_waits"] = fields[3]
            status["inno_mutex_rounds"] = fields[5]
            status["inno_mutex_os_waits"] = fields[8]
        elif line.startswith("RW-shared spins"):
            fields = line.split()
            status["inno_shrdrw_spins"] = fields[2]
            status["inno_shrdrw_rounds"] = fields[4]
            status["inno_shrdrw_os_waits"] = fields[7]
        elif line.startswith("RW-excl spins"):
            fields = line.split()
            status["inno_exclrw_spins"] = fields[2]
            status["inno_exclrw_rounds"] = fields[4]
            status["inno_exclrw_os_waits"] = fields[7]

    return

def get_innodb_status(cursor, status):
    query= "show engine innodb status"
    cursor.execute(query)

    for (type, name, innodb_status) in cursor:
        parse_innodb_status(innodb_status, status)
        break

    return

mysql_commands_section = StatusSection("cmds", [
StatusColumn("TPs", 0, column_flags_rate, field_handler_common, ["Com_commit", "Com_rollback"]),
StatusColumn("QPs", 3, column_flags_rate, field_handler_common, ["Com_select"]),
StatusColumn("DPs", 0, column_flags_rate, field_handler_common,["Com_delete"]),
StatusColumn("IPs", 0, column_flags_rate, field_handler_common,["Com_insert"]),
StatusColumn("UPs", 0, column_flags_rate, field_handler_common,["Com_update"]),
StatusColumn("DIUPs", 0, column_flags_rate, field_handler_common,["Com_delete","Com_insert","Com_update"])
])

mysql_net_section = StatusSection("net", [
StatusColumn("NetIn", 3, column_flags_rate|column_flags_bytes, field_handler_common,["Bytes_received"]),
StatusColumn("NetOut", 3, column_flags_rate|column_flags_bytes, field_handler_common, ["Bytes_sent"])
])

mysql_threads_section = StatusSection("threads_conns", [
StatusColumn("Run", 0, column_flags_none, field_handler_common, ["Threads_running"]),
StatusColumn("Create", 0, column_flags_rate, field_handler_common, ["Threads_created"]),
StatusColumn("Cache", 0, column_flags_none, field_handler_common, ["Threads_cached"]),
StatusColumn("Conns", 0, column_flags_none, field_handler_common, ["Threads_connected"]),
StatusColumn("Try", 3, column_flags_rate, field_handler_common, ["Connections"]),
StatusColumn("Abort", 0, column_flags_rate, field_handler_common, ["Aborted_connects"])
])

mysql_innodb_log_section = StatusSection("innodb_log", [
StatusColumn("HisList", 0, column_flags_none, field_handler_common, ["inno_history_list"]),
StatusColumn("Writen", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["inno_log_bytes_written"]),
StatusColumn("Flushed", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["inno_log_bytes_flushed"]),
StatusColumn("Checked", 0, column_flags_rate|column_flags_bytes, field_handler_common, ["inno_last_checkpoint"])
])

mysql_innodb_buffer_pool_usage_section = StatusSection("innodb_bp_usage", [
StatusColumn("DataPct", 0, column_flags_ratio, field_handler_common, ["Innodb_buffer_pool_pages_data","Innodb_buffer_pool_pages_total"]),
StatusColumn("Dirty", 0, column_flags_none, field_handler_common, ["Innodb_buffer_pool_pages_dirty"]),
StatusColumn("MReads", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_reads"]),
StatusColumn("Reads", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_read_requests"]),
StatusColumn("Writes", 0, column_flags_rate, field_handler_common, ["Innodb_buffer_pool_write_requests"])
])

def show_mysql_status(sections_name):
    mysql_sections = [
        mysql_commands_section,
        mysql_net_section,
        mysql_threads_section,
        mysql_innodb_log_section,
        mysql_innodb_buffer_pool_usage_section
        ]
    sections_to_show_default = [
        time_section,
        mysql_commands_section,
        mysql_net_section,
        mysql_threads_section
    ]

    sections_to_show = []

    if (len(sections_name) == 0):
        sections_to_show = sections_to_show_default
    else:
        for section_name in sections_name:
            find = 0
            if (find == 0):
                for section in common_sections:
                    if (section_name == section.getName()):
                        find = 1
                        sections_to_show.append(section)
                        break
            if (find == 0):
                for section in mysql_sections:
                    if (section_name == section.getName()):
                        find = 1
                        sections_to_show.append(section)
                        break

            if (find == 0):
                print "Section '%s' is not supported" % section_name
                print "Supported sections: " + get_supported_sections_name(mysql_sections)
                return

    if (len(sections_to_show) == 0):
        print "No section to show"
        return

    status = {}
    header_sections = get_sections_header(sections_to_show)
    header_columns = get_columns_header(sections_to_show)

    mysql_conn = mysql_connection_create()
    mysql_handler = get_mysql_handler(mysql_conn)

    # Init the first status
    get_mysql_status(mysql_handler, status)
    get_innodb_status(mysql_handler, status)
    get_status_line(sections_to_show, status)
    counter = 0

    while (1):
        status.clear()
        if (counter % 10 == 0):
            print header_sections
            print header_columns

        get_mysql_status(mysql_handler, status)
        get_innodb_status(mysql_handler, status)
        print get_status_line(sections_to_show, status)

        counter += 1
        time.sleep(interval)

    put_mysql_handler(mysql_handler)
    mysql_connection_destroy(mysql_conn)

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
    print '-s: sections to show'
    print '-t: show the time'

def version():
    return '0.1.0'

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvH:P:u:p:T:s:', ['help', 'version'])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    sections_name = []

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
            sections_name = arg.split(',')
        else:
            print 'Unhandled option'
            sys.exit(3)

    if (type == type_mysql):
        show_mysql_status(sections_name)