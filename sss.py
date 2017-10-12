#!/usr/bin/python

#Copyright (c) 2015, 2020. All rights reserved.
#
#This program is free software; you can redistribute it and/or modify
#it under the Apache License 2.0 License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#Author List
# name  email                 github                      blog
# deep  ieshen.zheng@163.com  https://github.com/deep011  https://deep011.github.io/

import time
import datetime
import getopt
import sys
import socket
import os

type_linux = "linux"
type_mysql = "mysql"
type_redis = "redis"
type_pika = "pika"
type_memcached = "memcached"
type_twemproxies = "twemproxies"
support_types=[type_linux,type_mysql,type_redis,type_pika,type_memcached,type_twemproxies]

service_type=type_linux

output_type_screen = 0  #Out put the status to the screen.
output_type_file = 1  #Out put the status to the files.
output_type_open_falcon = 2  #Out put the status to the open-falcon.
output_type = output_type_screen #default output is the screen.

output_file_name = ""
output_file = None
output_file_by_day = 0
date_format = "%Y-%m-%d"
time_format = "%H:%M:%S"
current_day = datetime.datetime.now().strftime(date_format)

open_falcon = "http://127.0.0.1:22230/v1/push"

speed_calculate_by_remote_monitor_system = 0


host="127.0.0.1"
port=3306
user="root"
password=""
socket_file=""

hostname=socket.gethostname()

status_collect_interval=1 #second, default is one second
status_collect_times=-1 #default is forever

#column_format = '%-*s'
column_format = '%*s'


all_section=0
sections_customized=0

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

def get_proc_pid_from_pid_file(pid_file):
    pidfile_fd = open(pid_file, 'r')
    process_pid = int(pidfile_fd.read(10))
    pidfile_fd.close()
    return process_pid

log_level_debug=0
log_level_info=1
log_level_error=2
log_level=log_level_info
if log_level == log_level_debug:
    import traceback
def get_exception_message(function_name, line_no, exception):
    exception_header = function_name + ":" + str(line_no) + " Exception: "
    if log_level == log_level_debug:
        exception_header += traceback.format_exc()
    elif log_level == log_level_info:
        exception_header += repr(exception)
    else:
        exception_header += str(exception)

    return exception_header

def get_falcon_metric_name_header(section_name):
    return service_type + "." + section_name

def get_falcon_tags_string(section_type):
    tags = ""
    if section_type == type_linux:
        tags += "linux"
    else:
        tags += "port=" + str(port)

    return tags

def append_server_alive_condition_to_falcon_json(server, status_json, server_alive):
    tags = get_falcon_tags_string(service_type)
    metric_name = get_falcon_metric_name_header("alive")

    status_json.append({
        "endpoint": hostname,
        "metric": metric_name,
        "timestamp": int(server.getCurrentTimeStamp()),
        "step": status_collect_interval,
        "value": float(server_alive),
        "counterType": "GAUGE",
        "tags": tags,
    },)

    return

errlog_file_name=""
def errlog(server, errstr, need_check_server_alive):
    if need_check_server_alive and server.check_alive != None:
        try:
            server_alive = server.check_alive(server)
            if output_type == output_type_open_falcon:
                status_json = []
                append_server_alive_condition_to_falcon_json(server, status_json, server_alive)
                output(server, json.dumps(status_json))
        except Exception, e:
            errlog(server, get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e), False)

        errstr += " " + "(" + service_type + " alive: " + str(server_alive) + ")"

    if len(errlog_file_name) == 0:
        print server.getCurrentTimeFormattedString() + " " + errstr
    else:
        errlog_file = open(errlog_file_name, 'a', 0)
        errlog_file.write(server.getCurrentDateTimeFormattedString() + " " + errstr + "\n")
        errlog_file.close()

    return

def output(server, content):
    if output_type == output_type_screen:
        print content
    elif output_type == output_type_file:
        output_file.write(content + '\n')
    elif output_type == output_type_open_falcon:
        r = requests.post(open_falcon, data=content)
        if r.text != "success":
            errlog(server, "ERROR: "+r.text, False)
        else:
            errlog(server, r.text, False)
    else:
        return

    return

def separate_output_file_if_needed(server):
    if (output_file_by_day == 1):
        today = server.current_time.strftime(date_format)
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
    def __init__(self, name, type, columns, status_get_functions, default_columns_name_show, instructions):
        self.name = name
        self.type = type
        self.columns = columns  #This section supported columns. This is a array of column.
        self.status_get_functions = status_get_functions
        self.default_columns_show = []
        self.columns_show = []    #Columns to show that in the self.columns. This is a array of column.
        self.instructions = instructions

        if default_columns_name_show == None or len(default_columns_name_show) == 0:
            self.default_columns_show = self.columns
        elif len(default_columns_name_show) == 1 and default_columns_name_show[0] == ALL_COLUMNS:
            self.default_columns_show = self.columns
        else:
            for column_name in  default_columns_name_show:
                for column in self.columns:
                    if (column_name == column.getName()):
                        self.default_columns_show.append(column)

            if len(self.default_columns_show) != len(default_columns_name_show):
                print "There are not supported columns name in the section initialization"
                sys.exit(3)

    def getName(self):
        return self.name
    def getType(self):
        return self.type
    def getColumns(self):
        return self.columns
    def getColumnsToShow(self):
        return self.columns_show
    def getInstructions(self):
        return self.instructions

    def setType(self, type):
        self.type = type
        return

    def clearColumnsToShow(self):
        self.columns_show = []
        return

    def isColumnAlreadyExistByName(self, column_name):
        for column_in in self.columns:
            if column_in.getName() == column_name:
                return 1

        return 0

    def isColumnAlreadyExist(self, column):
        return self.isColumnAlreadyExistByName(column.getName())

    def addColumn(self, column):
        if self.isColumnAlreadyExist(column) == 1:
            return 0

        self.columns.append(column)
        return 1

    def addColumnToShow(self,column_in):
        for column_show in self.columns_show:
            if (column_show.getName() == column_in.getName()):
                return 0

        for column in self.columns:
            if (column.getName() == column_in.getName()):
                self.columns_show.append(column)
                return 1

        return -1

    def addColumnsToShow(self,columns):
        for column_in in columns:
            find = 0
            for column in self.columns:
                if column_in.getName() == column.getName():
                    find = 1
                    break
            if find == 0:
                return -1   #There are not supported columns in the columns_name

        count = 0
        for column_in in columns:
            ret = self.addColumnToShow(column_in)
            count += ret

        if count == len(columns):
            return 2    #All columns in the columns_name are added.
        elif count > 0:
            return 1    #Some columns are not added.
        else:
            return 0    #No column was added.

    def addColumnToShowByName(self,column_name):
        for column in self.columns_show:
            if (column_name == column.getName()):
                return 0
        for column in self.columns:
            if (column_name == column.getName()):
                self.columns_show.append(column)
                return 1
        return -1

    def addColumnsToShowByName(self,columns_name):
        #Check all the columns name are corrent?
        for column_name in columns_name:
            find = 0
            for column in self.columns:
                if (column_name == column.getName()):
                    find = 1
                    break

            if find == 0:
                return -1   #There are not supported columns in the columns_name.

        count = 0
        for column_name in columns_name:
            ret = self.addColumnToShowByName(column_name)
            count += ret

        if count == len(columns_name):
            return 2    #All columns in the columns_name are added.
        elif count > 0:
            return 1    #Some columns are not added.
        else:
            return 0    #No column was added.

    def addColumnsDefaultToShow(self):
        return self.addColumnsToShow(self.default_columns_show)

    def addColumnsAllToShow(self):
        return self.addColumnsToShow(self.columns)

    def removeColumnFromShow(self,column_out):
        for column_show in self.columns_show:
            if (column_show.getName() == column_out.getName()):
                self.columns_show.remove(column_show)
                return 1

        for column in self.columns:
            if (column.getName() == column_out.getName()):
                return 0

        return -1

    def removeColumnsFromShow(self,columns):
        for column_out in columns:
            find = 0
            for column in self.columns:
                if column_out.getName() == column.getName():
                    find = 1
                    break
            if find == 0:
                return -1   #There are not supported columns in the columns_name

        count = 0
        for column_out in columns:
            ret = self.removeColumnFromShow(column_out)
            count += ret

        if count == len(columns):
            return 2    #All columns in the columns_name are added.
        elif count > 0:
            return 1    #Some columns are not added.
        else:
            return 0    #No column was added.

    def removeColumnFromShowByName(self,column_name):
        find = 0
        for column in self.columns:
            if (column_name == column.getName()):
                find = 1
        if find == 0:
            return -1

        for column in self.columns_show:
            if (column_name == column.getName()):
                self.columns_show.remove(column)
                return 1

        return 0

    def removeColumnsFromShowByName(self,columns_name):
        #Check all the columns name are corrent?
        for column_name in columns_name:
            find = 0
            for column in self.columns:
                if (column_name == column.getName()):
                    find = 1
                    break

            if find == 0:
                return -1   #There are not supported columns in the columns_name.

        count = 0
        for column_name in columns_name:
            ret = self.removeColumnFromShowByName(column_name)
            count += ret

        if count == len(columns_name):
            return 2    #All columns in the columns_name are removed.
        elif count > 0:
            return 1    #Some columns are not removed.
        else:
            return 0    #No column was removed.

    def removeColumnsDefaultFromShow(self):
        return self.removeColumnsFromShow(self.default_columns_show)

    def removeColumnsAllFromShow(self):
        return self.removeColumnsFromShow(self.columns)

    def getHeader(self):
        len_total = 0
        for column in self.columns_show:
            len_total += column.getWidth()

        if (len(self.name) == 0):
            return ' '*len_total

        len_half_left = (len_total-len(self.name))/2
        len_half_right = len_half_left
        if ((len_total-len(self.name))%2 == 1):
            len_half_right += 1

        return '-'*len_half_left+self.name+'-'*len_half_right

####### Class StatusColumn #######
column_flags_none=int('00000000',2)     # None flags. Default the fields are numbers.
column_flags_speed=int('00000001',2)    # The column is shown as speed.
column_flags_bytes=int('00000010',2)    # The column is shown as bytes.
column_flags_string=int('00000100',2)   # The fields are strings, otherwise are numbers; string can't be column_flags_speed.
column_flags_ratio=int('00001000',2)    # The column is shown as ratio.
column_flags_speed_then_ratio=int('00010000',2)    # The column is calculated by speed and then by ratio. Like (a_time2 - a_time1)/(b_time2 - b_time2)
class StatusColumn:
    def __init__(self, name, detail_name, blanks, flags, field_handler, fields, instructions):
        self.name = name
        self.detail_name = detail_name
        self.flags = flags
        self.field_handler = field_handler
        self.fields = fields
        self.instructions = instructions
        self.value_old = 0
        self.obj_old = None
        if (blanks > 0):   # Blanks is bigger than zero means we really want the blanks.
            self.width = len(name) + blanks
        elif (blanks == 0):   # Blanks is zero means the default blanks count between the columns, default is 2.
            self.width = len(name) + 1
            if (self.width < 8):
                self.width = 8
        else:
            self.width = len(name) + 2

    def getName(self):
        return self.name
    def getDetailName(self):
        return self.detail_name
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

    def getValue(self, column, status, server):
        value = column.field_handler(column, status, server)

        if column.getFlags() & column_flags_speed:
            if speed_calculate_by_remote_monitor_system == 1:
                return value

            interval_time = microsecond_differ_by_datetime(server.current_time, server.last_time)
            if (interval_time <= 0):
                interval_time = 1

            value_num = float(value)
            difference_value = value_num - column.getValueOld()
            column.setValueOld(value_num)
            rate = float(difference_value) * 1000000 / float(interval_time)
            value_str = "%3.1f" % rate
            return value_str

        return value


    def setValueOld(self, value):
        self.value_old = value
    def setObjOld(self, obj):
        self.obj_old = obj

## interval_time is microsecond
## The caller need to catch the exception
def field_handler_common(column, status, server):
    if (column.getFlags()&column_flags_ratio):
        fields = column.getFields()
        return "%.3f"%(float(status[fields[0]])*100/float(status[fields[1]]))

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

    if (column.getFlags()&column_flags_string == 0):
        value_str = str(value_num)

    return value_str

def get_status_line(server):
    line = ""

    for section in server.sections_to_show:
        if server.err > 0:
            break

        for column in section.getColumnsToShow():
            if server.err > 0:
                break

            try:
                value = column.getValue(column,server.status,server)
                if (column.getFlags()&column_flags_bytes):
                    value = byte2readable(value)
                elif (column.getFlags()&column_flags_string == 0 and column.getFlags()&column_flags_ratio == 0):
                    value = num2readable(value)

                line += column_format % (column.getWidth(),value)
            except Exception, e:
                server.err = 1
                server.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e)

        line += '|'

    if server.err > 0:
        return None

    return line

def get_status_falcon_json(server):
    status_json = []

    for section in server.sections_to_show:
        if server.err > 0:
            break

        tags = get_falcon_tags_string(section.getType())

        metric_name_header = get_falcon_metric_name_header(section.getName())

        for column in section.getColumnsToShow():
            if server.err > 0:
                break

            try:
                if column.getFlags()&column_flags_string:
                    continue
                if speed_calculate_by_remote_monitor_system == 1 and column.getFlags()&column_flags_speed_then_ratio:
                    continue

                counterType = "GAUGE"
                if speed_calculate_by_remote_monitor_system == 1 and column.getFlags()&column_flags_speed:
                    counterType = "COUNTER"

                metric_name = metric_name_header
                if len(column.getDetailName()) == 0:
                    metric_name += "." + column.getName()
                else:
                    metric_name += "." + column.getDetailName()

                status_json.append({
                    "endpoint": hostname,
                    "metric": metric_name,
                    "timestamp": int(server.getCurrentTimeStamp()),
                    "step": status_collect_interval,
                    "value": float(column.getValue(column,server.status,server)),
                    "counterType": counterType,
                    "tags": tags,
                },)
            except Exception, e:
                server.err = 1
                server.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e)

    if (server.err > 0):
        return None

    # No errors means server is alive.
    append_server_alive_condition_to_falcon_json(server, status_json, 1)

    return json.dumps(status_json)

####### Common #######
ALL_COLUMNS="all_columns"

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
        for column in section.getColumnsToShow():
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

def get_one_instructions(header, name, detail_name, instructions, max_line_len):
    line = name
    if len(detail_name) > 0:
        line += "("+detail_name+")"

    line += " : " + instructions
    lines = divide_one_line_to_multi_lines_by_max_length(line, max_line_len)

    one_instructions = header + "|" + lines[0]
    for line in lines[1:]:
        one_instructions += "\n"
        one_instructions += " " * len(header) + "|" + line

    return one_instructions

def get_section_instructions(section):
    global sections_customized
    max_line_len = 60
    header_section = "Section"
    header_column = "Column "

    section_instructions = get_one_instructions(header_section, section.getName(), "", section.getInstructions(), max_line_len)

    section_instructions += "\n" + "-"*segmentation_line_len + "\n"
    if sections_customized == 0:
        columns = section.getColumns()
    else:
        columns = section.getColumnsToShow()

    count = len(columns)
    for column in columns:
        section_instructions += get_one_instructions(header_column, column.getName(), column.getDetailName(), column.getInstructions(), max_line_len)
        count -= 1
        if (count >= 1):
            section_instructions += "\n" #+ "-"*segmentation_line_len + "\n"

    return section_instructions

#section part maybe like "section_name" or "section_name[column1_name,column2_name,column3_name]"
def extract_section_name_and_columns_name_from_section_part(section_part):
    if section_part.endswith("]") and section_part.find("[") >= 0:
        index = section_part.index("[")
        if (index == 0):
            return None

        columns_name=section_part[(index + 1):-1].split(",")
        section_name = section_part[0:index]
        return [section_name,columns_name]
    else:
        return [section_part]

#sections part maybe like "section1_name,section2_name[column1_name,column2_name,column3_name],section3_name[all_columns]"
def split_section_name_from_sections_part(sections_part):
    sections_name = []
    cursor=len(sections_part)
    while cursor > 0:
        if sections_part[cursor-1:cursor] == "]":
            try:
                idx = sections_part.rindex("[", 0, cursor)
            except Exception, e:
                return None

            if sections_part.rfind(",", 0, idx) < 0:
                sections_name.append(sections_part[0:cursor])
                sections_name.reverse()
                return sections_name

            idx_sub = sections_part.rindex(",", 0, idx)
            sections_name.append(sections_part[idx_sub+1:cursor])
            cursor = idx_sub
            continue
        else:
            if sections_part.rfind(",", 0, cursor) < 0:
                sections_name.append(sections_part[0:cursor])
                sections_name.reverse()
                return sections_name

            idx = sections_part.rindex(",", 0, cursor)
            sections_name.append(sections_part[idx + 1:cursor])
            cursor = idx
            continue

    return None

## The caller need to catch the exception
def field_handler_time(column, status, server):
    return server.getCurrentTimeFormattedString()

time_section = StatusSection("time", "other", [
StatusColumn("Time", "", 5, column_flags_string, field_handler_time, [], "Show the time when the status display.")
],[],[ALL_COLUMNS],"os time")

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

## The caller need to catch the exception
def field_handler_os_cpu(column, status, server):
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

os_cpu_section = StatusSection("os_cpu",type_linux,[
StatusColumn("usr", "user", 2, column_flags_string, field_handler_os_cpu, ["os_cpu_usr","os_cpu_total"], "Percentage of cpu user+nice time."),
StatusColumn("sys", "system", 2, column_flags_string, field_handler_os_cpu, ["os_cpu_sys","os_cpu_total"], "Percentage of cpu system+irq+softirq time."),
StatusColumn("idl", "idle", 3, column_flags_string, field_handler_os_cpu, ["os_cpu_idl","os_cpu_total"], "Percentage of cpu idle time."),
StatusColumn("iow", "iowait", 2, column_flags_string, field_handler_os_cpu, ["os_cpu_iow","os_cpu_total"], "Percentage of cpu iowait time.")
],[get_os_cpu_status],[ALL_COLUMNS],
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

os_load_section = StatusSection("os_load",type_linux,[
StatusColumn("1m", "1minute", 4, column_flags_string, field_handler_common, ["os_load_one"], "One minute average active tasks."),
StatusColumn("5m", "5minute", 4, column_flags_string, field_handler_common, ["os_load_five"], "Five minute average active tasks."),
StatusColumn("15m", "15minute", 3, column_flags_string, field_handler_common, ["os_load_fifteen"], "Fifteen minute average active tasks.")
],[get_os_load_status],[ALL_COLUMNS],
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

os_swap_section = StatusSection("os_swap",type_linux,[
StatusColumn("si", "swap_in_per_second", 4, column_flags_speed, field_handler_common, ["os_swap_pswpin"], "Counts per second of data moved from memory to swap, related to pswpin."),
StatusColumn("so", "swap_out_per_second", 4, column_flags_speed, field_handler_common, ["os_swap_pswpout"], "Counts per second of data moved from swap to memory, related to pswpout.")
],[get_os_swap_status],[ALL_COLUMNS],
"os swap status, collect from /proc/vmstat file")

net_face_name="lo"
def get_os_net_status(server, status):
    file = open("/proc/net/dev", 'r')
    line = file.readline().lstrip()

    find = 0
    while line:
        if (line.startswith(net_face_name+':')):
            find = 1
            fields = line.split()
            status["os_net_bytes_in"] = fields[1]
            status["os_net_bytes_out"] = fields[9]
            status["os_net_packages_in"] = fields[2]
            status["os_net_packages_out"] = fields[10]
            break
        
        line = file.readline().lstrip()

    file.close()

    if find == 0:
        errmsg = "Net face '" + net_face_name + "' is not exist!"
        raise Exception(errmsg)

    return

os_net_bytes_section = StatusSection("os_net_bytes",type_linux,[
StatusColumn("in", "incoming_bytes_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["os_net_bytes_in"], "Bytes per second the network incoming."),
StatusColumn("out", "outgoing_bytes_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["os_net_bytes_out"], "Bytes per second the network outgoing.")
],[get_os_net_status],[ALL_COLUMNS],
"os network bytes status, collect from /proc/net/dev file, you need to use --net-face option "
"to set the net face name that you want to monitor, the net face name is in the /proc/net/dev file")

os_net_packages_section = StatusSection("os_net_packages",type_linux,[
StatusColumn("in", "incoming_packages_per_second", 0, column_flags_speed, field_handler_common, ["os_net_packages_in"], "Packages per second the network incoming."),
StatusColumn("out", "outgoing_packages_per_second", 0, column_flags_speed, field_handler_common, ["os_net_packages_out"], "Packages per second the network outgoing.")
],[get_os_net_status],[ALL_COLUMNS],
"os network packages status, collect from /proc/net/dev file, you need to use --net-face option "
"to set the net face name that you want to monitor, the net face name is in the /proc/net/dev file")

disk_name = "vda"
os_disk_stats_first_time=1
def get_disk_status(server, status):
    file = open("/proc/diskstats", 'r')
    os_disk_stats_get_time = datetime.datetime.utcnow()
    line = file.readline()

    find = 0
    while line:
        fields = line.split()
        if (fields[2] == disk_name):
            find = 1
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

    if find == 0:
        errmsg = "Disk '" + disk_name + "' is not exist!"
        raise Exception(errmsg)

    return

os_disk_section = StatusSection("os_disk",type_linux,[
StatusColumn("reads", "", 0, column_flags_string, field_handler_common, ["os_disk_reads"], "Counts per second read from the disk."),
StatusColumn("writes", "", 0, column_flags_string, field_handler_common, ["os_disk_writes"], "Counts per second write to the disk."),
StatusColumn("rbytes", "", 0, column_flags_string, field_handler_common, ["os_disk_read_bytes"], "Bytes per second read from the disk."),
StatusColumn("wbytes", "", 0, column_flags_string, field_handler_common, ["os_disk_write_bytes"], "Bytes per second write to the disk."),
StatusColumn("queue", "", 2, column_flags_string, field_handler_common, ["os_disk_queue"], "Disk queue length per second."),
StatusColumn("await", "", 2, column_flags_string, field_handler_common, ["os_disk_wait"], "Average milliseconds of queue and service time for each read/write."),
StatusColumn("svctm", "", 2, column_flags_string, field_handler_common, ["os_disk_service_time"], "Average milliseconds of service time for each read/write."),
StatusColumn("%util", "", 1, column_flags_string, field_handler_common, ["os_disk_busy"], "Disk utilization percent.")
],[get_disk_status],[ALL_COLUMNS],
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

os_mem_section = StatusSection("os_mem",type_linux,[
StatusColumn("total", "", 0, column_flags_bytes, field_handler_common, ["os_mem_total"],"Total memory size bytes."),
StatusColumn("free", "", 0, column_flags_bytes, field_handler_common, ["os_mem_free"],"Free memory size bytes."),
StatusColumn("buffer", "", 0, column_flags_bytes, field_handler_common, ["os_mem_buffers"],"Buffered memory size bytes."),
StatusColumn("cached", "", 0, column_flags_bytes, field_handler_common, ["os_mem_cached"],"Cached memory size bytes.")
], [get_os_mem_status],[ALL_COLUMNS],
"os memory status, collect from /proc/meminfo file")

proc_pid = 0
proc_pidfile = ""
proc_pid_is_set = 0
def get_proc_cpu_status(server, status):
    global proc_pid_is_set
    global proc_pid
    if (proc_pid_is_set == 0):
        proc_pid = server.getPidNum(server)
        if server.err == 1:
            return

        proc_pid_is_set = 1

    try:
        filename = "/proc/"+str(proc_pid)+"/stat"
        file = open(filename, 'r')
    except IOError, e:
        proc_pid_is_set = 0 # Need get the proc pid next time.
        errmsg = "Proc id '" + str(proc_pid) + "' is not exist!"
        raise Exception(errmsg)
        return

    line = file.readline()
    file.close()

    fields = line.split()
    utime = long(fields[13])
    stime = long(fields[14])
    cutime = long(fields[15])
    cstime = long(fields[16])

    status["proc_cpu"] = utime + stime
    return

proc_cpu_section = StatusSection("proc_cpu","", [
StatusColumn("%cpu", "cpu_utilization", 0, column_flags_speed, field_handler_common, ["proc_cpu"], "Cpu utilization per second.")
], [get_proc_cpu_status],[ALL_COLUMNS],
"process cpu status, collect from /proc/[pid]/stat file, usually the pid should automatically "
"get from the server.getPidNum() function, but you can also replace the pid by the --proc-pid option")

def get_proc_mem_status(server, status):
    global proc_pid_is_set
    global proc_pid
    if (proc_pid_is_set == 0):
        proc_pid = server.getPidNum(server)
        if server.err == 1:
            return

        proc_pid_is_set = 1

    try:
        filename = "/proc/"+str(proc_pid)+"/status"
        file = open(filename, 'r')
    except IOError, e:
        server.err = 1
        server.errmsg = "Error can not open file: " + filename
        proc_pid_is_set = 0 # Need get the proc pid next time.
        return

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

proc_mem_section = StatusSection("proc_mem", "",[
StatusColumn("rss", "resident_memory", 0, column_flags_bytes, field_handler_common, ["proc_mem_res"], "Bytes for resident memory size of the process in."),
StatusColumn("vsz", "virtual_memory", 0, column_flags_bytes, field_handler_common, ["proc_mem_virt"], "Bytes for virtual memory size of the process in.")
], [get_proc_mem_status],[ALL_COLUMNS],
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
        self.last_time = datetime.datetime.now() # microsecond
        self.current_time = datetime.datetime.now() # microsecond
        self.err = 0
        self.errmsg = ""
        self.need_reinit = 0
        self.check_alive = None    #check_alive()

    def getName(self):
        return self.name

    def getType(self):
        return self.type

    def getCurrentTimeStamp(self):
        return time.mktime(self.current_time.timetuple())

    def getCurrentTimeFormattedString(self):
        return column_format % (9, self.current_time.strftime(time_format))

    def getCurrentDateTimeFormattedString(self):
        return column_format % (9, self.current_time.strftime(date_format+" "+time_format))

    def getPidNum(self, server):
        if len(proc_pidfile) > 0:
            return get_proc_pid_from_pid_file(proc_pidfile)

        if self.getPidNumHandler == None:
            print "Please set the process pid number"
            sys.exit(3)

        try:
            pid_num = self.getPidNumHandler(server)
        except Exception, e:
            server.err = 1
            server.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e)
            pid_num = -1

        return pid_num

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
        for section in sections:
            self.addSectionToShowByName(section.getName())

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

    def addSection(self, section):
        for section_in in self.sections:
            if (section.getName() == section_in.getName()):
                return 0

        self.sections.append(section)
        return 1

    def removeSectionByName(self, section_name):
        self.removeSectionFromShowByName(section_name)

        for section_in in self.sections:
            if (section_name == section_in.getName()):
                self.sections.remove(section_in)
                return 1

        return 0


    def addSectionToShowByName(self, section_name):
        #section_name maybe contain column names like "section_name[column_name1,column_name2,column_name3]"
        section_part = extract_section_name_and_columns_name_from_section_part(section_name)
        columns_name = None
        if section_part == None:
            return -1
        elif len(section_part) == 2:
            section_name = section_part[0]
            columns_name = section_part[1]

        #Check if the section is already exsited.
        for section in self.sections_to_show:
            if (section.getName() == section_name):
                ret = 0
                if columns_name == None:
                    if all_section == 1 or output_type == output_type_open_falcon:
                        ret = section.addColumnsAllToShow()
                    else:
                        ret = section.addColumnsDefaultToShow()
                elif len(columns_name) == 1 and columns_name[0] == ALL_COLUMNS:
                    ret = section.addColumnsAllToShow()
                else:
                    ret = section.addColumnsToShowByName(columns_name)

                if ret == -1:
                    return -1
                if ret > 0:
                    return 1
                else:
                    return 0

        section = self.getSectionByName(section_name)
        if section == None:
            return -1

        ret = 0
        if columns_name == None:
            if all_section == 1 or output_type == output_type_open_falcon:
                ret = section.addColumnsAllToShow()
            else:
                ret = section.addColumnsDefaultToShow()
        elif len(columns_name) == 1 and columns_name[0] == ALL_COLUMNS:
            ret = section.addColumnsAllToShow()
        else:
            ret = section.addColumnsToShowByName(columns_name)

        if ret == -1:
            return -1

        self.sections_to_show.append(section)
        self.addSectionStatusGetFunctions(section)
        return 1

    def removeSectionFromShowByName(self, section_name):
        # section_name maybe contain column names like "section_name[column_name1,column_name2,column_name3]"
        section_part = extract_section_name_and_columns_name_from_section_part(section_name)
        columns_name = None
        if section_part == None:
            return -1   #section_name format is error.
        elif len(section_part) == 2:
            section_name = section_part[0]
            columns_name = section_part[1]

        if (self.isSectionSupported(section_name) == False):
            return -1   #This section is not supported.

        #Delete it if the section is exsited.
        for section in self.sections_to_show:
            if (section.getName() == section_name):
                ret = 0
                if columns_name == None:
                    ret = section.removeColumnsDefaultFromShow()
                elif len(columns_name) == 1 and columns_name[0] == ALL_COLUMNS:
                    ret = section.removeColumnsAllFromShow()
                else:
                    ret = section.removeColumnsFromShowByName(columns_name)

                if ret == -1:
                    return -1   #Some column name are not supported.

                if len(section.getColumnsToShow()) == 0:
                    self.sections_to_show.remove(section)
                    self.removeSectionStatusGetFunctions(section)
                    return 2    #This section was removed.

                if ret > 0:
                    return 1    #Some columns were removed from this section.

        return 0    #Nothing was removed.

    def setTypeSectionsToShowIfNeeded(self):
        for section in self.sections_to_show:
            if section.getType() == "":
                section.setType(service_type)

        return

    def initStatus(self):
        for section in self.sections_to_show:
            for column in section.columns:
                for field in column.getFields():
                    self.status[field] = -1

        return

    def getStatus(self):
        self.initStatus()
        for func in self.status_get_funcs:
            if self.err > 0:
                break

            try:
                func[0](self,self.status)
            except Exception, e:
                self.err = 1
                self.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e) + " IN Function " + getattr(func[0],'__name__')

        return

    def showStatus(self):
        self.header_sections = get_sections_header(self.sections_to_show)
        self.header_columns = get_columns_header(self.sections_to_show)

        # Init the first status
        self.getStatus()
        get_status_line(self)
        if (self.err > 0):
            errlog(self, self.errmsg, True)

        counter = -1
        while (1):
            counter += 1
            if status_collect_times >= 0 and counter >= status_collect_times:
                return

            time.sleep(status_collect_interval)
            self.status.clear()

            # update the server time
            self.last_time = self.current_time
            self.current_time = datetime.datetime.now()

            if (separate_output_file_if_needed(self) == 1 or counter % 10 == 0):
                output(self, self.header_sections)
                output(self, self.header_columns)

            if (self.err > 0):
                self.err = 0
                try:
                    if self.clean != None:
                        self.clean(self)
                    if self.initialize != None:
                        self.initialize(self)
                    self.need_reinit = 1
                except Exception, e:
                    self.err = 1
                    self.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e)
                    errlog(self, self.errmsg, True)
                    continue

                # Reinit the first status
                self.getStatus()
                get_status_line(self)
                time.sleep(0.1)
                self.need_reinit = 0
                if self.err > 0:
                    errlog(self, self.errmsg, True)
                    continue

            self.getStatus()
            status_line = get_status_line(self)
            if self.err > 0:
                errlog(self, self.errmsg, True)
                continue

            output(self, status_line)

        return

    def uploadToOpenFalcon(self):
        # Init the first status
        self.getStatus()
        if (self.err > 0):
            errlog(self, self.errmsg, True)

        # If speed calculate by the  remote monitor system, and status only collect one time,
        # we just return the status without sleep.
        if speed_calculate_by_remote_monitor_system == 1 and status_collect_times == 1:
            status_line = get_status_falcon_json(self)
            if self.err > 0:
                errlog(self, self.errmsg, True)
                return

            output(self, status_line)
            return

        counter = -1
        while (1):
            counter += 1
            if status_collect_times >= 0 and counter >= status_collect_times:
                return

            time.sleep(status_collect_interval)
            self.status.clear()

            # update the server time
            self.last_time = self.current_time
            self.current_time = datetime.datetime.now()

            if (self.err > 0):
                self.err = 0
                try:
                    if self.clean != None:
                        self.clean(self)
                    if self.initialize != None:
                        self.initialize(self)
                    self.need_reinit = 1
                except Exception, e:
                    self.err = 1
                    self.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e)
                    errlog(self, self.errmsg, True)
                    continue

                # Reinit the first status
                self.getStatus()
                time.sleep(0.1)
                self.need_reinit = 0
                if self.err > 0:
                    errlog(self, self.errmsg, True)
                    continue

            self.getStatus()
            status_line = get_status_falcon_json(self)
            if self.err > 0:
                errlog(self, self.errmsg, True)
                continue

            output(self, status_line)

        return

# Mysql monitor implemented by deep
####### Mysql Implement #######
def mysql_connection_create():
    import mysql.connector

    if len(socket_file) == 0:
        mysql_conn = mysql.connector.connect(
            user=user,
            password=password,
            host=host,
            port=port)
    else:
        mysql_conn = mysql.connector.connect(
            user=user,
            password=password,
            unix_socket=socket_file)

    return mysql_conn

def mysql_connection_destroy(conn):
    conn.close()
    return

def get_mysql_handler(conn):
    return conn.cursor()

def put_mysql_handler(handler):
    handler.close()
    return

def check_mysql_alive(server):
    alive = 0
    try:
        query= "select 1"
        conn = mysql_connection_create()
        handler = get_mysql_handler(conn)
        handler.execute(query)
        for (value, ) in handler:
            alive = value
            break
    except Exception, e:
        return alive

    put_mysql_handler(handler)
    mysql_connection_destroy(conn)
    return alive

## The caller need to catch the exception
def get_mysql_status(server, status):
    query= "show global status"
    server.cursor.execute(query)
    for (variable_name, value) in server.cursor:
        status[variable_name] = value
    return

## The caller need to catch the exception
def get_mysql_replication_status(server, status):
    query= "show slave status"
    server.cursor.execute(query)

    status["role"] = 0
    status["slave_io_running"] = 0
    status["slave_sql_running"] = 0
    status["seconds_behind_master"] = 0
    status["relay_log_space"] = 0

    row = server.cursor.fetchone()
    if (row == None):
        return

    status["role"] = 1
    row_dict = dict(zip(server.cursor.column_names, row))

    if row_dict["Slave_IO_Running"] == "Yes":
        status["slave_io_running"] = 1
    else:
        status["slave_io_running"] = 0

    if row_dict["Slave_SQL_Running"] == "Yes":
        status["slave_sql_running"] = 1
    else:
        status["slave_sql_running"] = 0

    if row_dict["Seconds_Behind_Master"] == "NULL" or row_dict["Seconds_Behind_Master"] == None:
        status["seconds_behind_master"] = -1
    else:
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

## The caller need to catch the exception
def get_innodb_status(server, status):
    query= "show engine innodb status"
    server.cursor.execute(query)

    for (type, name, innodb_status) in server.cursor:
        parse_innodb_status(innodb_status, status)
        break

    return

## The caller need to catch the exception
def mysql_initialize_for_server(server):
    server.conn = mysql_connection_create()
    server.cursor = get_mysql_handler(server.conn)
    return

## The caller need to catch the exception
def mysql_clean_for_server(server):
    put_mysql_handler(server.cursor)
    mysql_connection_destroy(server.conn)
    return

## The caller need to catch the exception
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

mysql_command_section = StatusSection("command","", [
StatusColumn("QPs", "select_per_second", 0, column_flags_speed, field_handler_common, ["Com_select"], "Select commands per second. Collected from 'Com_select'. If a query result is returned from query cache, the server increments the Qcache_hits status variable, not Com_select."),
StatusColumn("DPs", "delete_per_second", 0, column_flags_speed, field_handler_common,["Com_delete"], "Delete commands per second. Collected from 'Com_delete'."),
StatusColumn("IPs", "insert_per_second", 0, column_flags_speed, field_handler_common,["Com_insert"], "Insert commands per second. Collected from 'Com_insert'."),
StatusColumn("UPs", "update_per_second", 0, column_flags_speed, field_handler_common,["Com_update"], "Update commands per second. Collected from 'Com_update'."),
StatusColumn("DMPs", "delete_multi_per_second", 0, column_flags_speed, field_handler_common,["Com_delete_multi"], "Delete commands per second that use multiple-table syntax. Collected from 'Com_delete_multi'."),
StatusColumn("UMPs", "update_multi_per_second", 0, column_flags_speed, field_handler_common,["Com_update_multi"], "Update commands per second that use multiple-table syntax. Collected from 'Com_update_multi'."),
StatusColumn("TPs", "transactions_per_second", 0, column_flags_speed, field_handler_common, ["Com_commit", "Com_rollback"], "Transactions per second. Collected from the sum of 'Com_commit' and 'Com_rollback'."),
StatusColumn("DIUPs", "dml_per_second", 0, column_flags_speed, field_handler_common,["Com_delete","Com_insert","Com_update"], "DDL(delete+insert+update) commands per second. Collected from the sum of 'Com_delete', 'Com_insert' and 'Com_update'."),
StatusColumn("LPs", "load_per_second", 0, column_flags_speed, field_handler_common,["Com_load"], "Load commands per second. Collected from 'Com_load'."),
StatusColumn("ATPs", "alter_table_per_second", 0, column_flags_speed, field_handler_common,["Com_alter_table"], "Alter table commands per second. Collected from 'Com_alter_table'.")
], [get_mysql_status],["TPs","QPs","DPs","IPs","UPs","DIUPs"],
"mysql commands status, collect from \'show global status\'")

mysql_net_section = StatusSection("net", "",[
StatusColumn("NetIn", "incoming_bytes_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common,["Bytes_received"], "Bytes per second received from all clients."),
StatusColumn("NetOut", "outgoing_bytes_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["Bytes_sent"], "Bytes per second sent to all clients.")
], [get_mysql_status],[ALL_COLUMNS],
"mysql network status, collect from \'show global status\'")

mysql_threads_section = StatusSection("threads_conns", "",[
StatusColumn("Run", "threads_running", 0, column_flags_none, field_handler_common, ["Threads_running"], "The number of threads that are not sleeping."),
StatusColumn("Create", "threads_created_per_second", 0, column_flags_speed, field_handler_common, ["Threads_created"], "Counts per second of threads created to handle connections."),
StatusColumn("Cache", "threads_cached", 0, column_flags_none, field_handler_common, ["Threads_cached"], "The number of threads in the thread cache."),
StatusColumn("Conns", "connections", 0, column_flags_none, field_handler_common, ["Threads_connected"], "The number of currently open connections."),
StatusColumn("Try", "try_to_connects_per_second", 0, column_flags_speed, field_handler_common, ["Connections"], "Counts per second of connection attempts (successful or not) to the MySQL server."),
StatusColumn("Abort", "aborted_clients_per_second", 0, column_flags_speed, field_handler_common, ["Aborted_connects"], "Counts per second of failed attempts to connect to the MySQL server.")
], [get_mysql_status],[ALL_COLUMNS],
"mysql thread status, collect from \'show global status\'")

mysql_innodb_redo_log_section = StatusSection("innodb_redo_log", "",[
StatusColumn("Written", "bytes_written_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["redo_log_bytes_written"], "Bytes per second redo log data written."),
StatusColumn("Flushed", "bytes_flushed_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["redo_log_bytes_flushed"], "Bytes per second redo log data flushed."),
StatusColumn("Checked", "bytes_checked_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["redo_log_last_checkpoint"], "Bytes per second redo log data checked.")
], [get_innodb_status],[ALL_COLUMNS],
"mysql innodb redo log status, collect from \'show engine innodb status\'")

mysql_innodb_log_section = StatusSection("innodb_log", "",[
StatusColumn("HisList", "history_list_length", 0, column_flags_none, field_handler_common, ["inno_history_list"], "History list length."),
StatusColumn("Fsyncs", "fsync_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_os_log_fsyncs"], "Counts per second of fsync() writes done to the log file."),
StatusColumn("Written", "bytes_written_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["Innodb_os_log_written"], "Bytes per second written to the log file.")
], [get_mysql_status, get_innodb_status],[ALL_COLUMNS],
"mysql innodb redo log status, collect from \'show global status\' and \'show engine innodb status\'")

mysql_innodb_buffer_pool_usage_section = StatusSection("innodb_bp_usage", "",[
StatusColumn("DataPct", "data_pages_percentage", 0, column_flags_ratio, field_handler_common, ["Innodb_buffer_pool_pages_data","Innodb_buffer_pool_pages_total"], "Data pages percentage of possession in total pages."),
StatusColumn("Dirty", "dirty_pages", 0, column_flags_none, field_handler_common, ["Innodb_buffer_pool_pages_dirty"], "The number of pages currently dirty."),
StatusColumn("DReads", "disk_reads_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_buffer_pool_reads"], "Counts per second of logical reads that InnoDB could not satisfy from the buffer pool, and had to read directly from the disk."),
StatusColumn("Reads", "logical_reads_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_buffer_pool_read_requests"], "Counts per second of logical read requests."),
StatusColumn("Writes", "writes_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_buffer_pool_write_requests"], "Counts per second of writes done to the InnoDB buffer pool.")
], [get_mysql_status],[ALL_COLUMNS],
"mysql innodb buffer pool status, collect from \'show global status\'")

mysql_innodb_rows_section = StatusSection("innodb_rows", "",[
StatusColumn("Insert", "inserted_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_rows_inserted"], "Counts per second of rows inserted into InnoDB tables."),
StatusColumn("Update", "updated_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_rows_updated"], "Counts per second of rows updated in InnoDB tables."),
StatusColumn("Delete", "deleted_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_rows_deleted"], "Counts per second of rows deleted in InnoDB tables."),
StatusColumn("Read", "read_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_rows_read"], "Counts per second of rows read from InnoDB tables.")
], [get_mysql_status],[ALL_COLUMNS],
"mysql innodb rows status, collect from \'show global status\'")

mysql_innodb_data_section = StatusSection("innodb_data", "",[
StatusColumn("Reads", "reads_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_data_reads"], "Counts per second of data reads (OS file reads)."),
StatusColumn("Writes", "writes_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_data_writes"], "Counts per second of data writes."),
StatusColumn("Read", "bytes_read_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["Innodb_data_read"], "Bytes per second data read."),
StatusColumn("Written", "bytes_write_per_second", 0, column_flags_speed|column_flags_bytes, field_handler_common, ["Innodb_data_written"], "Bytes per second data written.")
], [get_mysql_status],[ALL_COLUMNS],
"mysql innodb data status, collect from \'show global status\'")

mysql_innodb_row_lock_section = StatusSection("row_lock", "",[
StatusColumn("LWaits", "waits_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_row_lock_waits"], "Times per second "
    "a row lock had to be waited for."),
StatusColumn("LTime", "milliseconds_locked_per_second", 0, column_flags_speed, field_handler_common, ["Innodb_row_lock_time"], "Milliseconds spent "
    "in acquiring row locks among one second.")
], [get_mysql_status],[ALL_COLUMNS],
"mysql row lock status, collect from \'show global status\'")

mysql_table_lock_section = StatusSection("table_lock", "",[
StatusColumn("LWait", "table_lock_waited_per_second", 0, column_flags_speed, field_handler_common, ["Table_locks_waited"], "Times per second that "
    "a request for a table lock could not be granted immediately and a wait was needed. If this is high "
    "and you have performance problems, you should first optimize your queries, and then either split "
    "your table or tables or use replication."),
StatusColumn("LImt", "table_lock_immediate_granted_per_second", 0, column_flags_speed, field_handler_common, ["Table_locks_immediate"], "Times per second "
    "that a request for a table lock could be granted immediately.")
], [get_mysql_status],[ALL_COLUMNS],
"mysql table lock status, collect from \'show global status\'")

mysql_innodb_internal_lock_section = StatusSection("innodb_internal_lock", "",[
StatusColumn("MSpin", "mutex_spin_waits_per_second", 0, column_flags_speed, field_handler_common, ["inno_mutex_spin_waits"], "Times per second "
    "the Mutex spin waits."),
StatusColumn("MRound", "mutex_rounds_per_second", 0, column_flags_speed, field_handler_common, ["inno_mutex_rounds"], "Times per second the "
    "threads looped in the spin-wait cycle for Mutex."),
StatusColumn("MOWait", "mutex_os_waits_per_second", 0, column_flags_speed, field_handler_common, ["inno_mutex_os_waits"], "Times per second "
    "the thread gave up spin-waiting and went to sleep instead for Mutex."),
StatusColumn("SSpin", "rw_shared_spin_waits_per_second", 0, column_flags_speed, field_handler_common, ["inno_shrdrw_spins"], "Times per second the "
    "RW-shared spin waits."),
StatusColumn("SRound", "rw_shared_spin_rounds_per_second", 0, column_flags_speed, field_handler_common, ["inno_shrdrw_rounds"], "Times per second "
    "the threads looped in the spin-wait cycle for RW-shared."),
StatusColumn("SOWait", "rw_shared_spin_os_waits_per_second", 0, column_flags_speed, field_handler_common, ["inno_shrdrw_os_waits"], "Times per second "
    "the thread gave up spin-waiting and went to sleep instead for RW-shared."),
StatusColumn("ESpin", "rw_excl_spin_waits_per_second", 0, column_flags_speed, field_handler_common, ["inno_exclrw_spins"], "Times per second the "
    "RW-excl spin waits."),
StatusColumn("ERound", "rw_excl_spin_rounds_per_second", 0, column_flags_speed, field_handler_common, ["inno_exclrw_rounds"], "Times per second "
    "the threads looped in the spin-wait cycle for RW-excl."),
StatusColumn("EOWait", "rw_excl_spin_os_waits_per_second", 0, column_flags_speed, field_handler_common, ["inno_exclrw_os_waits"], "Times per second "
    "the thread gave up spin-waiting and went to sleep instead for RW-excl.")
], [get_innodb_status],[ALL_COLUMNS],
"mysql innodb internal lock status, collect from \'show engine innodb status\'")

mysql_replication_section = StatusSection("repl", "",[
StatusColumn("r", "role", 1, column_flags_none, field_handler_common, ["role"], "Value is \'0\' if the instance is a master, or \'1\' if the instance is enslaved to a master(it is a slave). Note that a slave can be master of another slave (daisy chaining)."),
StatusColumn("ir", "slave_io_running", 2, column_flags_none, field_handler_common, ["slave_io_running"], "If the role is a slave, this is the 'Slave_IO_Running', 0 means 'No' and 1 means 'Yes'."),
StatusColumn("sr", "slave_sql_running", 2, column_flags_none, field_handler_common, ["slave_sql_running"], "If the role is a slave, this is the 'Slave_SQL_Running', 0 means 'No' and 1 means 'Yes'."),
StatusColumn("Delay", "seconds_behind_master", 0, column_flags_none, field_handler_common, ["seconds_behind_master"], "This is the \'Seconds_Behind_Master\', "
    "based on the timestamps stored in events, measures the time difference in seconds between the slave SQL thread and the "
    "slave I/O thread. If the network connection between master and slave is fast, the slave I/O thread is very close to "
    "the master, so this field is a good approximation of how late the slave SQL thread is compared to the master. "
    "If the network is slow, this is not a good approximation; the slave SQL thread may quite often be caught up with "
    "the slow-reading slave I/O thread, so Seconds_Behind_Master often shows a value of 0, even if the I/O thread is "
    "late compared to the master. In other words, this column is useful only for fast networks."),
StatusColumn("RSpace", "relay_log_space", 0, column_flags_bytes, field_handler_common, ["relay_log_space"], "The total combined size of all existing relay log files.")
], [get_mysql_replication_status],[ALL_COLUMNS],
"mysql replication status, collect from \'show slave status\'")

mysql_handler_section = StatusSection("handler", "",[
StatusColumn("Write", "write_per_second", 0, column_flags_speed, field_handler_common, ["Handler_write"], "Requests per second to insert a row in a table."),
StatusColumn("Update", "update_per_second", 0, column_flags_speed, field_handler_common, ["Handler_update"], "Requests per second to update a row in a table."),
StatusColumn("Del", "delete_per_second", 0, column_flags_speed, field_handler_common, ["Handler_delete"], "Times per second that rows have been deleted from tables"),
StatusColumn("First", "read_first_per_second", 0, column_flags_speed, field_handler_common, ["Handler_read_first"], "Times per second the first entry in an index was read. If this value is high, it suggests that the server is doing a lot of full index scans; for example, SELECT col1 FROM foo, assuming that col1 is indexed."),
StatusColumn("Key", "read_key_per_second", 0, column_flags_speed, field_handler_common, ["Handler_read_key"], "Requests per second to read a row based on a key. If this value is high, it is a good indication that your tables are properly indexed for your queries."),
StatusColumn("Last", "read_last_per_second", 0, column_flags_speed, field_handler_common, ["Handler_read_last"], "Requests per second to read the last key in an index. With ORDER BY, the server will issue a first-key request followed by several next-key requests, whereas with ORDER BY DESC, the server will issue a last-key request followed by several previous-key requests. This variable was added in MySQL 5.5.7."),
StatusColumn("Next", "read_next_per_second", 0, column_flags_speed, field_handler_common, ["Handler_read_next"], "Requests per second to read the next row in key order. This value is incremented if you are querying an index column with a range constraint or if you are doing an index scan."),
StatusColumn("Prev", "read_prev_per_second", 0, column_flags_speed, field_handler_common, ["Handler_read_prev"], "Requests per second to read the previous row in key order. This read method is mainly used to optimize ORDER BY ... DESC."),
StatusColumn("Rnd", "read_rnd_per_second", 0, column_flags_speed, field_handler_common, ["Handler_read_rnd"], "Requests per second to read a row based on a fixed position. This value is high if you are doing a lot of queries that require sorting of the result. You probably have a lot of queries that require MySQL to scan entire tables or you have joins that do not use keys properly."),
StatusColumn("RNext", "read_rnd_next_per_second", 0, column_flags_speed, field_handler_common, ["Handler_read_rnd_next"], "Requests per second to read the next row in the data file. This value is high if you are doing a lot of table scans. Generally this suggests that your tables are not properly indexed or that your queries are not written to take advantage of the indexes you have."),
StatusColumn("Commit", "commit_per_second", 0, column_flags_speed, field_handler_common, ["Handler_commit"], "Counts per second of internal COMMIT statements."),
StatusColumn("Pre", "prepare_per_second", 0, column_flags_speed, field_handler_common, ["Handler_prepare"], "Counts per second of the prepare phase of two-phase commit operations."),
StatusColumn("Rback", "rollback_per_second", 0, column_flags_speed, field_handler_common, ["Handler_rollback"], "Requests per second for a storage engine to perform a rollback operation."),
StatusColumn("Spoint", "savepoint_per_second", 0, column_flags_speed, field_handler_common, ["Handler_savepoint"], "Requests per second for a storage engine to place a savepoint."),
StatusColumn("SPRb", "savepoint_rollback_per_second", 0, column_flags_speed, field_handler_common, ["Handler_savepoint_rollback"], "Requests per second for a storage engine to roll back to a savepoint."),
StatusColumn("ELock", "external_lock_per_second", 0, column_flags_speed, field_handler_common, ["Handler_external_lock"], "Times per second for each call to its external_lock() function, which generally occurs at the beginning and end of access to a table instance. There might be differences among storage engines. This variable can be used, for example, to discover for a statement that accesses a partitioned table how many partitions were pruned before locking occurred: Check how much the counter increased for the statement, subtract 2 (2 calls for the table itself), then divide by 2 to get the number of partitions locked."),
StatusColumn("MInit", "mrr_init_per_second", 0, column_flags_speed, field_handler_common, ["Handler_mrr_init"], "Times per second for the server uses a storage engine's own Multi-Range Read implementation for table access.")
], [get_mysql_status],["Write","Update","Del","Commit"],
"mysql handler status, collect from \'show global status\' about \'Handler_*\' variables")

mysql_sections = [
mysql_command_section,
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
mysql_replication_section,
mysql_handler_section
]
mysql_sections_to_show_default = [
time_section,
mysql_command_section,
mysql_net_section,
mysql_threads_section
]

# Redis monitor implemented by deep
####### Redis Implement #######
def redis_connection_create():
    import redis.connection
    redis_conn = redis.StrictRedis(
        host=host,
        port=port,
        password=password)

    return redis_conn

def redis_connection_destroy(conn):
    conn.connection_pool.disconnect()
    return

## The caller need to catch the exception
def redis_initialize_for_server(server):
    server.redis_conn = redis_connection_create()
    return

## The caller need to catch the exception
def redis_clean_for_server(server):
    redis_connection_destroy(server.redis_conn)
    return

def check_redis_alive(server):
    alive = 0
    try:
        conn = redis_connection_create()
        r = conn.ping()
        if r == True:
            alive = 1
    except Exception, e:
        return alive

    redis_connection_destroy(conn)
    return alive

## The caller need to catch the exception
def redis_get_pidnum_for_server(server):
    pid = server.redis_conn.info()["process_id"]
    return int(pid)

## The caller need to catch the exception
def get_redis_status(server, status):
    redis_info = server.redis_conn.info()
    for key in redis_info:
        status[key] = redis_info[key]

    # Calculate the keyspace status
    keys_count = 0
    expires_count = 0
    for idx in range(10000):
        if (status.has_key("db" + str(idx)) == False):
            break;

        db_message = status["db" + str(idx)]
        keys_count += long(db_message["keys"])
        expires_count += long(db_message["expires"])

    status["keys"] = keys_count
    status["expires"] = expires_count

    return

redis_command_attributes_flags_none=int('0000',2)  # None flags.
redis_command_attributes_flags_write=int('0001',2)  # Write command flags.
redis_command_attributes_flags_readonly=int('0010',2)  # Readonly command flags.

cached_redis_command_attributes=0
def init_redis_command_attributes_if_needed(server):
    global cached_redis_command_attributes
    if cached_redis_command_attributes == 1:
        return

    cached_redis_command_attributes = 1
    server.redis_commands_attributes = {}

    try:
        redis_commands_info = server.redis_conn.execute_command("command")
    except Exception, e:
        if e.args[0] == "unknown command 'command'":
            return
        else:
            raise

    for command_info in redis_commands_info:
        command_name = command_info[0]
        command_attributes = command_info[2]
        if (server.redis_commands_attributes.has_key(command_name) == False):
            server.redis_commands_attributes[command_name] = redis_command_attributes_flags_none
        for attribute in command_attributes:
            if (attribute == "readonly"):
                server.redis_commands_attributes[command_name] |= redis_command_attributes_flags_readonly
            elif (attribute == "write"):
                server.redis_commands_attributes[command_name] |= redis_command_attributes_flags_write

    return

redis_command_full_section_name = "command_full"
def get_redis_command_full_section(server, status, command_name, calls):
    if output_type == output_type_screen or output_type == output_type_file:
        return

    command_full_section = server.getSectionByName(redis_command_full_section_name)
    
    if command_full_section == None:
        command_full_section = StatusSection(redis_command_full_section_name, type_redis, [], [],[ALL_COLUMNS], 
            "redis full command status, collect from \'info commandstat\' and \'command\'")
        server.addSection(command_full_section)
        server.addSectionToShowByName(redis_command_full_section_name)
    
    column_name = command_name
    field_name = "redis_commands_" + command_name + "_count"
    
    if command_full_section.isColumnAlreadyExistByName(column_name) == 0:
        command_column = StatusColumn(command_name, command_name+"_per_second", 0, column_flags_speed, field_handler_common,
            [field_name],
            "Number of "+command_name+" command processed per second.")
        
        command_full_section.addColumn(command_column)
        command_full_section.addColumnToShowByName(column_name)

    status[field_name] = calls

    return

redis_command_fetch_method_from_info=0
redis_command_fetch_method_from_info_commandstats=1
redis_command_fetch_method=redis_command_fetch_method_from_info_commandstats
def get_redis_command_status_from_info_commandstats(server, status):
    all_commands_count = 0
    readonly_commands_count = 0
    write_commands_count = 0

    global redis_command_fetch_method

    try:
        redis_info_commandstats = server.redis_conn.info("commandstats")
    except Exception, e:
        if e.args[0] == "wrong number of arguments for 'info' command":
            redis_command_fetch_method = redis_command_fetch_method_from_info
            return
        else:
            raise

    for key in redis_info_commandstats:
        calls = redis_info_commandstats[key]["calls"]

        all_commands_count += calls
        command_name = key.split("_")[1]

        get_redis_command_full_section(server, status, command_name, calls)

        if len(server.redis_commands_attributes) > 0:
            if server.redis_commands_attributes[command_name] & redis_command_attributes_flags_readonly:
                readonly_commands_count += calls
            elif server.redis_commands_attributes[command_name] & redis_command_attributes_flags_write:
                write_commands_count += calls

    status["redis_commands_readonly_count"] = readonly_commands_count
    status["redis_commands_write_count"] = write_commands_count
    status["redis_commands_all_count"] = all_commands_count

    return

def get_redis_command_status_from_info(server, status):
    # Nothing to do, because qps fetched from 'total_commands_processed' from the info command response.
    return

## The caller need to catch the exception
def get_redis_command_status(server, status):
    global cached_redis_command_attributes
    global redis_command_fetch_method
    if (server.need_reinit == 1):
        cached_redis_command_attributes = 0
        redis_command_fetch_method = redis_command_fetch_method_from_info_commandstats
        server.removeSectionByName(redis_command_full_section_name)

    init_redis_command_attributes_if_needed(server)

    if redis_command_fetch_method==redis_command_fetch_method_from_info_commandstats:
        get_redis_command_status_from_info_commandstats(server,status)
    elif redis_command_fetch_method==redis_command_fetch_method_from_info:
        get_redis_command_status_from_info(server, status)

    return

## The caller need to catch the exception
def field_handler_redis_qps(column, status, server):
    global redis_command_fetch_method
    if redis_command_fetch_method==redis_command_fetch_method_from_info_commandstats:
        return status["redis_commands_all_count"]
    elif redis_command_fetch_method==redis_command_fetch_method_from_info:
        return status["total_commands_processed"]

    return -1

## The caller need to catch the exception
def field_handler_redis_replication(column, status, server):

    ## init the values assumed this is a master
    role = 0
    link_status = 0
    slaves_count = status["connected_slaves"]

    ## change the values if this is a slave
    if status["role"] == "slave":
        role = 1
        if status["master_link_status"] == "up":
            link_status = 1

    if column.getName() == "r":
        return role
    elif column.getName() == "s":
        return slaves_count
    elif column.getName() == "l":
        return link_status

    return ""

redis_connection_section = StatusSection("connection", "",[
StatusColumn("conns", "connected_clients", 0, column_flags_none, field_handler_common, ["connected_clients"], "Counts for connected clients."),
StatusColumn("receive", "received_per_second", 0, column_flags_speed, field_handler_common, ["total_connections_received"], "Number of connections accepted by the server per second."),
StatusColumn("reject", "rejected_per_second", 0, column_flags_speed, field_handler_common, ["rejected_connections"], "Number of connections rejected because of maxclients limit per second.")
], [get_redis_status],[ALL_COLUMNS],
"redis connection status, collect from \'info\'")

redis_client_section = StatusSection("client", "",[
StatusColumn("LOList", "client_longest_output_list", 0, column_flags_none, field_handler_common, ["client_longest_output_list"], "Longest client output list length."),
StatusColumn("BIBuf", "client_biggest_input_buf", 0, column_flags_bytes, field_handler_common, ["client_biggest_input_buf"], "Biggest client input buffer size in bytes.")
], [get_redis_status],[ALL_COLUMNS],
"redis client status, collect from \'info\'")

redis_memory_section = StatusSection("mem", "",[
StatusColumn("used", "used_memory", 0, column_flags_bytes, field_handler_common, ["used_memory"], "Total number of bytes allocated by Redis using its allocator (either standard libc, jemalloc, or an alternative allocator such as tcmalloc."),
StatusColumn("rss", "used_memory_rss", 0, column_flags_bytes, field_handler_common, ["used_memory_rss"], "Number of bytes that Redis allocated as seen by the operating system (a.k.a resident set size). This is the number reported by tools such as top(1) and ps(1)."),
StatusColumn("peak", "used_memory_peak", 0, column_flags_bytes, field_handler_common, ["used_memory_peak"], "Peak memory consumed by Redis (in bytes).")
], [get_redis_status],[ALL_COLUMNS],
"redis memory usage, collect from \'info\'")

redis_net_section = StatusSection("net", "",[
StatusColumn("in", "incoming_bytes_per_second", 0, column_flags_bytes|column_flags_speed, field_handler_common, ["total_net_input_bytes"], "Bytes per second received into redis."),
StatusColumn("out", "outgoing_bytes_per_second", 0, column_flags_bytes|column_flags_speed, field_handler_common, ["total_net_output_bytes"], "Bytes per second sent by redis.")
], [get_redis_status],[ALL_COLUMNS],
"redis network status, collect from \'info\'")

redis_keyspace_section = StatusSection("keyspace", "",[
StatusColumn("keys", "", 0, column_flags_none, field_handler_common, ["keys"], "Number of keys in all db."),
StatusColumn("expires", "", 0, column_flags_none, field_handler_common, ["expires"], "Number of keys with an expiration in all db.")
], [get_redis_status],[ALL_COLUMNS],
"redis keyspace status, collect from \'info\'")

redis_key_section = StatusSection("key", "",[
StatusColumn("hits", "hits_per_second", 0, column_flags_speed, field_handler_common, ["keyspace_hits"], "Count per second of successful lookup of keys in the main dictionary."),
StatusColumn("misses", "misses_per_second", 0, column_flags_speed, field_handler_common, ["keyspace_misses"], "Count per second of failed lookup of keys in the main dictionary."),
StatusColumn("expired", "expired_per_second", 0, column_flags_speed, field_handler_common, ["expired_keys"], "Number of key expiration events among one second."),
StatusColumn("evicted", "evicted_per_second", 0, column_flags_speed, field_handler_common, ["evicted_keys"], "Number of evicted keys due to maxmemory limit among one second.")
], [get_redis_status],[ALL_COLUMNS],
"redis key status, collect from \'info\'")

redis_command_section = StatusSection("command", "",[
StatusColumn("cmds", "commands_per_second", 0, column_flags_speed, field_handler_redis_qps, ["redis_commands_all_count","total_commands_processed"], "Number of commands processed per second."),
StatusColumn("reads", "read_commands_per_second", 0, column_flags_speed, field_handler_common, ["redis_commands_readonly_count"], "Number of readonly commands processed per second."),
StatusColumn("writes", "write_commands_per_second", 0, column_flags_speed, field_handler_common, ["redis_commands_write_count"], "Number of write commands processed per second.")
], [get_redis_command_status,get_redis_status],[ALL_COLUMNS],
"redis command status, collect from \'info commandstat\' and \'command\'")

redis_persistence_section = StatusSection("persis", "",[
StatusColumn("ln", "loading_data", 1, column_flags_none, field_handler_common, ["loading"], "Flag indicating if the load of a dump file is on-going."),
StatusColumn("rn", "rdb_bgsaving", 1, column_flags_none, field_handler_common, ["rdb_bgsave_in_progress"], "Flag indicating a RDB save is on-going."),
StatusColumn("an", "aof_rewriting", 1, column_flags_none, field_handler_common, ["aof_rewrite_in_progress"], "Flag indicating a AOF rewrite operation is on-going.")
], [get_redis_status],[ALL_COLUMNS],
"redis persistence status, collect from \'info\'")

redis_replication_section = StatusSection("repl","",[
StatusColumn("r", "role", 1, column_flags_none, field_handler_redis_replication, ["role"], "Value is \'0\' if the instance is slave of no one(it is a master), or \'1\' if the instance is enslaved to a master(it is a slave). Note that a slave can be master of another slave (daisy chaining)."),
StatusColumn("s", "slaves_count", 1, column_flags_none, field_handler_redis_replication, ["connected_slaves"], "This value means the number of connected slaves."),
StatusColumn("l", "link_status", 1, column_flags_none, field_handler_redis_replication, ["master_link_status"], "If the role is slave, this value is the status of the replication link, 0 means 'down' and 1 means 'up'")
], [get_redis_status],[ALL_COLUMNS],
"redis replication status, collect from \'info\'")

redis_sections = [
redis_connection_section,
redis_client_section,
redis_memory_section,
redis_net_section,
redis_keyspace_section,
redis_key_section,
redis_command_section,
redis_persistence_section,
redis_replication_section
]

redis_sections_to_show_default = [
time_section,
proc_cpu_section,
redis_command_section,
redis_memory_section,
redis_net_section,
redis_connection_section
]

# Pika monitor implemented by deep
####### Pika Implement #######
def pika_connection_create():
    import redis.connection
    try:
        pika_conn = redis.StrictRedis(
            host=host,
            port=port,
            password=password)
    except Exception,e:
        server.err = 1
        server.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e)

    return pika_conn

def pika_connection_destroy(conn):
    return

## The caller need to catch the exception
def pika_initialize_for_server(server):
    server.pika_conn = pika_connection_create()
    return

## The caller need to catch the exception
def pika_clean_for_server(server):
    redis_connection_destroy(server.pika_conn)
    return

## The caller need to catch the exception
def pika_get_pidnum_for_server(server):
    pid = server.pika_conn.info("server")["process_id"]
    return int(pid)

## The caller need to catch the exception
def get_pika_status(server, status):
    pika_info = server.pika_conn.info()
    for key in pika_info:
        status[key] = pika_info[key]

    return

## The caller need to catch the exception
def field_handler_pika_keyspace(column, status, server):
    string_key_count = long(status["kv keys"])
    hash_key_count = long(status["hash keys"])
    list_key_count = long(status["list keys"])
    zset_key_count = long(status["zset keys"])
    set_key_count = long(status["set keys"])

    if (column.getName() == "keys"):
        return string_key_count+hash_key_count+list_key_count+zset_key_count+set_key_count
    elif (column.getName() == "string"):
        return string_key_count
    elif (column.getName() == "hash"):
        return hash_key_count
    elif (column.getName() == "list"):
        return list_key_count
    elif (column.getName() == "zset"):
        return zset_key_count
    elif (column.getName() == "set"):
        return set_key_count

    return "0"

## The caller need to catch the exception
def field_handler_pika_replication(column, status, server):
    ## init the values assumed this is a master
    role = 0
    link_status = 0
    slaves_count = status["connected_slaves"]
    if slaves_count < 0:
        slaves_count = 0

    ## change the values if this is a slave
    if status["role"] == "slave":
        role = 1
        if status["master_link_status"] == "up":
            link_status = 1

    if column.getName() == "r":
        return role
    elif column.getName() == "s":
        return slaves_count
    elif column.getName() == "l":
        return link_status

    return ""

pika_connection_section = StatusSection("connection", "",[
StatusColumn("conns", "connected_clients", 0, column_flags_none, field_handler_common, ["connected_clients"], "Counts for connected clients."),
StatusColumn("receive", "received_per_second", 0, column_flags_speed, field_handler_common, ["total_connections_received"], "Number of connections accepted by the server per second.")
], [get_pika_status],[ALL_COLUMNS],
"pika connection status, collect from \'info\'")

pika_data_section = StatusSection("data", "",[
StatusColumn("DBSize", "data_size", 0, column_flags_bytes, field_handler_common, ["db_size"], "Total number of bytes used by Pika in the data directory."),
StatusColumn("UMem", "used_memory", 0, column_flags_bytes, field_handler_common, ["used_memory"], "Total number of bytes allocated by Pika using its allocator (either standard libc, jemalloc, or an alternative allocator such as tcmalloc."),
StatusColumn("MTable", "db_memtable_usage", 0, column_flags_bytes, field_handler_common, ["db_memtable_usage"], "Total number of bytes allocated for the Pika memtable.")
], [get_pika_status],[ALL_COLUMNS],
"pika disk and memory usage, collect from \'info\'")

pika_keyspace_section = StatusSection("keyspace", "",[
StatusColumn("keys", "all_keys_count", 0, column_flags_none, field_handler_pika_keyspace, [], "Number of all keys."),
StatusColumn("string", "string_keys_count", 0, column_flags_none, field_handler_pika_keyspace, [], "Number of string keys."),
StatusColumn("hash", "hash_keys_count", 0, column_flags_none, field_handler_pika_keyspace, [], "Number of hash keys."),
StatusColumn("list", "list_keys_count", 0, column_flags_none, field_handler_pika_keyspace, [], "Number of list keys."),
StatusColumn("zset", "zset_keys_count", 0, column_flags_none, field_handler_pika_keyspace, [], "Number of zset keys."),
StatusColumn("set", "set_keys_count", 0, column_flags_none, field_handler_pika_keyspace, [], "Number of set keys."),
], [get_pika_status],["keys"],
"pika keyspace status, collect from \'info\'")

pika_command_section = StatusSection("command", "",[
StatusColumn("cmds", "commands_per_second", 0, column_flags_speed, field_handler_common, ["total_commands_processed"], "Number of commands processed per second.")
], [get_pika_status],[ALL_COLUMNS],
"pika command status, collect from \'info\'")

pika_replication_section = StatusSection("repl", "",[
StatusColumn("r", "role", 1, column_flags_none, field_handler_pika_replication, ["role"], "Value is \'0\' if the instance is slave of no one(it is a master), or \'1\' if the instance is enslaved to a master(it is a slave). Note that a slave can be master of another slave (daisy chaining)."),
StatusColumn("s", "slaves_count", 1, column_flags_none, field_handler_pika_replication, ["connected_slaves"], "This value means the number of connected slaves."),
StatusColumn("l", "link_status", 1, column_flags_none, field_handler_pika_replication, ["master_link_status"], "If the role is slave, this value is the status of the replication link, 0 means 'down' and 1 means 'up'")
], [get_pika_status],[ALL_COLUMNS],
"pika replication status, collect from \'info\'")

pika_sections = [
pika_connection_section,
pika_data_section,
pika_keyspace_section,
pika_command_section,
pika_replication_section
]

pika_sections_to_show_default = [
time_section,
pika_connection_section,
pika_command_section,
pika_data_section,
pika_keyspace_section,
pika_replication_section
]

# Memcached monitor implemented by deep
####### Memcached Implement #######
def memcached_connection_create():
    import memcache
    address = host + ":" + str(port)
    mc_conn = memcache.Client([address]);
    return mc_conn

def memcached_connection_destroy(conn):
    return

## The caller need to catch the exception
def memcached_initialize_for_server(server):
    server.mc_conn = memcached_connection_create()
    return

## The caller need to catch the exception
def memcached_clean_for_server(server):
    memcached_connection_destroy(server.mc_conn)
    return

def check_memcached_alive(server):
    alive = 0

    try:
        cmd = "version\r\n"
        memcached_check_alive_mark_header = "VERSION"

        sd = socket.socket()
        sd.settimeout(1)
        sd.connect((host, port))

        sd.send(cmd)
        buf = sd.recv(128)
        if len(buf) > len(memcached_check_alive_mark_header) and buf.startswith(memcached_check_alive_mark_header) == True:
            alive = 1
    except Exception, e:
        return alive

    sd.close()
    return alive

## The caller need to catch the exception
def memcached_get_pidnum_for_server(server):
    pid = server.mc_conn.get_stats()[0][1]["pid"]
    return int(pid)

## The caller need to catch the exception
def get_memcached_status(server, status):
    memcached_info = server.mc_conn.get_stats()[0][1]
    for key in memcached_info:
        status[key] = memcached_info[key]
    return

## The caller need to catch the exception
def field_handler_memcached_hits_percentage(column, status, server):
    fields = column.getFields()

    values = []
    for i in range(0, len(fields)):
        values.append(status[fields[i]])

    obj = column.getObjOld()
    if obj == None:
        column.setObjOld(values)
        return '0'

    values_diff = []
    for i in range(0, len(fields)):
        values_diff.append(long(values[i]) - long(obj[i]))

    column.setObjOld(values)
    all_diff = float(0)
    for i in range(0, len(fields)):
        all_diff += float(values_diff[i])

    if all_diff == 0:
        return '0'

    return "%3.1f"%(float(values_diff[0])/all_diff * 100)

memcached_connection_section = StatusSection("connection", "",[
StatusColumn("conns", "connected_clients", 0, column_flags_none, field_handler_common, ["curr_connections"], "Counts for connected clients."),
StatusColumn("receive", "received_per_second", 0, column_flags_speed, field_handler_common, ["total_connections"], "Number of connections accepted by the server per second.")
], [get_memcached_status],[ALL_COLUMNS],
"memcached connection status, collect from \'stats\'")

memcached_net_section = StatusSection("net", "",[
StatusColumn("in", "incoming_bytes_per_second", 0, column_flags_bytes|column_flags_speed, field_handler_common, ["bytes_read"], "Bytes per second received into memcached."),
StatusColumn("out", "outgoing_bytes_per_second", 0, column_flags_bytes|column_flags_speed, field_handler_common, ["bytes_written"], "Bytes per second sent by memcached.")
], [get_memcached_status],[ALL_COLUMNS],
"memcached network status, collect from \'stats\'")

memcached_command_section = StatusSection("command", "",[
StatusColumn("get", "get_per_second", 0, column_flags_speed, field_handler_common, ["cmd_get"], "Number of retrieval commands processed per second. Retrieval commands include get, gets and so on."),
StatusColumn("set", "set_per_second", 0, column_flags_speed, field_handler_common, ["cmd_set"], "Number of storage commands processed per second. Storage commands include set, add, replace, append, prepend, cas and so on."),
StatusColumn("del", "delete_per_second", 0, column_flags_speed, field_handler_common, ["delete_misses", "delete_hits"], "Number of delete commands processed per second."),
StatusColumn("ari", "arithmetic_per_second", 0, column_flags_speed, field_handler_common, ["incr_misses", "incr_hits", "decr_misses", "decr_hits"], "Number of arithmetic commands processed per second. Arithmetic commands include incr, decr and so on"),
StatusColumn("flu", "flush_all_per_second", 0, column_flags_speed, field_handler_common, ["cmd_flush"], "Number of flush_all commands processed per second.")
], [get_memcached_status],["get","set","del","ari"],
"memcached command status, collect from \'stats\'")

memcached_command_detail_section = StatusSection("command_detail", "",[
StatusColumn("GetH", "get_hits_per_second", 0, column_flags_speed, field_handler_common, ["get_hits"], "Number of retrieval commands hits per second. Retrieval commands include get, gets and so on."),
StatusColumn("GetM", "get_misses_per_second", 0, column_flags_speed, field_handler_common, ["get_misses"], "Number of retrieval commands misses per second. Retrieval commands include get, gets and so on."),
StatusColumn("DelH", "delete_hits_per_second", 0, column_flags_speed, field_handler_common, ["delete_hits"], "Number of delete commands hits per second."),
StatusColumn("DelM", "delete_misses_per_second", 0, column_flags_speed, field_handler_common, ["delete_misses"], "Number of delete commands misses per second."),
StatusColumn("IncH", "incr_hits_per_second", 0, column_flags_speed, field_handler_common, ["incr_hits"], "Number of incr commands hits per second."),
StatusColumn("IncM", "incr_misses_per_second", 0, column_flags_speed, field_handler_common, ["incr_misses"], "Number of incr commands misses per second."),
StatusColumn("DecH", "decr_hits_per_second", 0, column_flags_speed, field_handler_common, ["decr_hits"], "Number of decr commands hits per second."),
StatusColumn("DecM", "decr_misses_per_second", 0, column_flags_speed, field_handler_common, ["decr_misses"], "Number of decr commands misses per second."),
StatusColumn("CasH", "cas_hits_per_second", 0, column_flags_speed, field_handler_common, ["cas_hits"], "Number of cas commands hits per second."),
StatusColumn("CasM", "cas_misses_per_second", 0, column_flags_speed, field_handler_common, ["cas_misses"], "Number of cas commands misses per second."),
StatusColumn("CasB", "cas_badval_per_second", 0, column_flags_speed, field_handler_common, ["cas_badval"], "Number of cas commands bad values per second."),
StatusColumn("GetPct", "get_percentage", 0, column_flags_speed_then_ratio, field_handler_memcached_hits_percentage, ["cmd_get", "cmd_set", "incr_misses", "incr_hits", "decr_misses", "decr_hits"], "Percentage of retrieval commands among all the retrieval, storage and arithmetic commands per second."),
StatusColumn("GetHPct", "get_hits_percentage", 0, column_flags_speed_then_ratio, field_handler_memcached_hits_percentage, ["get_hits","get_misses"], "Hits percentage of retrieval commands per second. Retrieval commands include get, gets and so on."),
StatusColumn("DelHPct", "delete_hits_percentage", 0, column_flags_speed_then_ratio, field_handler_memcached_hits_percentage, ["delete_hits","delete_misses"], "Hits percentage of delete commands per second."),
StatusColumn("IncHPct", "incr_hits_percentage", 0, column_flags_speed_then_ratio, field_handler_memcached_hits_percentage, ["incr_hits","incr_misses"], "Hits percentage of incr commands per second."),
StatusColumn("DecHPct", "decr_hits_percentage", 0, column_flags_speed_then_ratio, field_handler_memcached_hits_percentage, ["decr_hits","decr_misses"], "Hits percentage of decr commands per second."),
StatusColumn("CasHPct", "cas_hits_percentage", 0, column_flags_speed_then_ratio, field_handler_memcached_hits_percentage, ["cas_hits","cas_misses","cas_badval"], "Hits percentage of cas commands per second.")
], [get_memcached_status],["GetPct","GetHPct"],
"memcached command detail status, collect from \'stats\'")

memcached_sections = [
memcached_connection_section,
memcached_net_section,
memcached_command_section,
memcached_command_detail_section
]

memcached_sections_to_show_default = [
time_section,
proc_cpu_section,
memcached_command_section,
memcached_command_detail_section,
memcached_connection_section,
memcached_net_section
]

# Twemproxies monitor implemented by deep
####### Twemproxies Implement #######
def twemproxies_connection_create():
    sd = socket.socket()
    sd.settimeout(1)
    sd.connect((host, port))
    return sd

def twemproxies_connection_destroy(conn):
    conn.close()
    return

## The caller need to catch the exception
def twemproxies_initialize_for_server(server):
    server.tws_conn = twemproxies_connection_create()
    return

## The caller need to catch the exception
def twemproxies_clean_for_server(server):
    if hasattr(server, 'tws_conn'):
        twemproxies_connection_destroy(server.tws_conn)

    return

## The caller need to catch the exception
def twemproxies_get_pidnum_for_server(server):
    return -1

def parse_twemproxies_server_status(server_status,status):
    status["requests"] += long(server_status["requests"])
    status["request_bytes"] += long(server_status["request_bytes"])
    status["responses"] += long(server_status["responses"])
    status["response_bytes"] += long(server_status["response_bytes"])

    status["in_queue"] += long(server_status["in_queue"])
    status["in_queue_bytes"] += long(server_status["in_queue_bytes"])
    status["out_queue"] += long(server_status["out_queue"])
    status["out_queue_bytes"] += long(server_status["out_queue_bytes"])

    status["server_connections"] += long(server_status["server_connections"])
    status["server_eof"] += long(server_status["server_eof"])
    status["server_timedout"] += long(server_status["server_timedout"])
    status["server_err"] += long(server_status["server_err"])
    if long(server_status["server_ejected_at"]) > status["server_ejected_at"]:
        status["server_ejected_at"] = long(server_status["server_ejected_at"]) 
    
    return

def parse_twemproxies_pool_status(pool_status,status):
    status["client_eof"] += long(pool_status["client_eof"])
    status["client_err"] += long(pool_status["client_err"])
    status["client_connections"] += long(pool_status["client_connections"])
    status["server_ejects"] += long(pool_status["server_ejects"])
    status["forward_error"] += long(pool_status["forward_error"])
    status["fragments"] += long(pool_status["fragments"])


    status["requests"] = 0
    status["request_bytes"] = 0
    status["responses"] = 0
    status["response_bytes"] = 0

    status["in_queue"] = 0
    status["in_queue_bytes"] = 0
    status["out_queue"] = 0
    status["out_queue_bytes"] = 0

    status["server_connections"] = 0
    status["server_eof"] = 0
    status["server_timedout"] = 0
    status["server_err"] = 0
    status["server_ejected_at"] = 0

    for key,value in pool_status.items():
        if  type(value) is dict:
            parse_twemproxies_server_status(value,status)
    return

def parse_twemproxies_status(tws_status,status):
    status["curr_connections"] = tws_status["curr_connections"]
    status["total_connections"] = tws_status["total_connections"]

    status["client_eof"] = 0
    status["client_err"] = 0
    status["client_connections"] = 0
    status["server_ejects"] = 0
    status["forward_error"] = 0
    status["fragments"] = 0
    for key, value in tws_status.items():
        if  type(value) is dict:
            parse_twemproxies_pool_status(value,status)

    return

## The caller need to catch the exception
def get_twemproxies_status(server, status):
    cmd = "status\r\n"
    n_send = server.tws_conn.send(cmd)
    if n_send != len(cmd):
        return

    buf = ""
    while 1:
        data = server.tws_conn.recv(1024)
        if not data:
            # connection close, let's kill it and raise
            raise Exception("connection closed by server")

        buf += data
        if buf.endswith("\n"):
            break

    tws_status = json.loads(buf)

    parse_twemproxies_status(tws_status, status)
    return

twemproxies_connection_section = StatusSection("connection", "",[
StatusColumn("conns", "connected_clients", 0, column_flags_none, field_handler_common, ["curr_connections"], "Counts for current connections."),
StatusColumn("receive", "received_per_second", 0, column_flags_speed, field_handler_common, ["total_connections"], "Number of connections accepted by the proxy per second.")
], [get_twemproxies_status],[ALL_COLUMNS],
"twemproxies connection status, collect from \'status\'")

twemproxies_client_section = StatusSection("client", "",[
StatusColumn("conns", "connected_clients", 0, column_flags_none, field_handler_common, ["client_connections"], "Counts for connected clients."),
StatusColumn("eof", "client_eof_per_second", 0, column_flags_speed, field_handler_common, ["client_eof"], "Number of client eof per second."),
StatusColumn("err", "client_err_per_second", 0, column_flags_speed, field_handler_common, ["client_err"], "Number of client error per second.")
], [get_twemproxies_status],[ALL_COLUMNS],
"twemproxies client status, collect from \'status\'")

twemproxies_server_section = StatusSection("server", "",[
StatusColumn("conns", "server_connections", 0, column_flags_none, field_handler_common, ["server_connections"], "Counts of connections for backend servers."),
StatusColumn("eof", "server_eof_per_second", 0, column_flags_speed, field_handler_common, ["server_eof"], "Number of backend server eof per second."),
StatusColumn("err", "server_err_per_second", 0, column_flags_speed, field_handler_common, ["server_err"], "Number of backend server error per second."),
StatusColumn("tio", "server_timedout_per_second", 0, column_flags_speed, field_handler_common, ["server_timedout"], "Number of backend server timeout per second."),
StatusColumn("eje", "server_ejects_per_second", 0, column_flags_speed, field_handler_common, ["server_ejects"], "Number of backend server ejected per second.")
], [get_twemproxies_status],[ALL_COLUMNS],
"twemproxies backend server status, collect from \'status\'")

twemproxies_command_section = StatusSection("command", "",[
StatusColumn("req", "requests_per_second", 0, column_flags_speed, field_handler_common, ["requests"], "Number of requests received from clients per second."),
StatusColumn("resp", "responses_per_second", 0, column_flags_speed, field_handler_common, ["responses"], "Number of responses sent to clients per second."),
StatusColumn("resp", "responses_per_second", 0, column_flags_speed, field_handler_common, ["fragments"], "Number of fragments processed per second. Fragments created from a multi-vector request, like mget, mset and delete multi keys.")
], [get_twemproxies_status],[ALL_COLUMNS],
"twemproxies command status, collect from \'status\'")

twemproxies_net_section = StatusSection("net", "",[
StatusColumn("in", "incoming_bytes_per_second", 0, column_flags_bytes|column_flags_speed, field_handler_common, ["request_bytes"], "Bytes per second received into the proxy."),
StatusColumn("out", "outgoing_bytes_per_second", 0, column_flags_bytes|column_flags_speed, field_handler_common, ["response_bytes"], "Bytes per second sent by the proxy.")
], [get_twemproxies_status],[ALL_COLUMNS],
"twemproxies network status, collect from \'status\'")

twemproxies_queue_section = StatusSection("queue", "",[
StatusColumn("req", "requests_cached", 0, column_flags_none, field_handler_common, ["in_queue"], "Counts of requests cached in the proxy."),
StatusColumn("resp", "responses_cached", 0, column_flags_none, field_handler_common, ["out_queue"], "Counts of responses cached in the proxy."),
StatusColumn("ReqB", "request_bytes_cached", 0, column_flags_bytes, field_handler_common, ["in_queue_bytes"], "Bytes of requests cached in the proxy."),
StatusColumn("RespB", "response_bytes_cached", 0, column_flags_bytes, field_handler_common, ["out_queue_bytes"], "Bytes of responses cached in the proxy.")
], [get_twemproxies_status],["req","resp"],
"twemproxies queue status, collect from \'status\'")

twemproxies_sections = [
twemproxies_connection_section,
twemproxies_client_section,
twemproxies_server_section,
twemproxies_command_section,
twemproxies_net_section,
twemproxies_queue_section
]

twemproxies_sections_to_show_default = [
time_section,
twemproxies_connection_section,
twemproxies_client_section,
twemproxies_command_section,
twemproxies_net_section,
twemproxies_queue_section
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
    print '-T: target service type, default is '+support_types[0]
    print '-s: sections to show, use comma to split'
    print '-a: addition sections to show, use comma to split'
    print '-d: removed sections for the showing, use comma to split'
    print '-I,--instructions: show the support sections\' instructions'
    print '-o: output the status to this file'
    print '-D: separate output files by day, suffix of the file name is \'_yyyy-mm-dd\''
    print '-e: output error message to this file'
    print '-i: time interval to show the status, unit is second'
    print '-n: the count of the status to collect, default is forever'
    print '-S: speed is calculated by the remote monitor system, like the open-falcon'
    print '--socket: the socket file to use for connection'
    print '--falcon: upload the status to the open-falcon, the address is like \''+open_falcon+'\''
    print '--net-face: set the net device face name for os_net_* sections, default is \'lo\''
    print '--disk-name: set the disk device name for os_disk sections, default is \'vda\''
    print '--proc-pid: set the process pid number for proc_* sections, default is 0'
    print '\r\n'
    support_services=""
    for service in support_types:
        support_services+=service+" "
    print 'Support services: '+support_services
    print ''

def version():
    return '0.2.0'

def print_version():
    print "sss version " + version()
    return

def print_sections_instructions(server):
    global sections_customized
    segmentation_line = "_"*segmentation_line_len
    if sections_customized == 0:
        sections = server.getSupportedSections()
    else:
        sections = server.sections_to_show

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
        opts, args = getopt.getopt(sys.argv[1:], 'hvIH:P:u:p:T:s:a:d:o:De:i:n:S', ['help', 'version', 'instructions','socket=','falcon=','net-face=','disk-name=','proc-pid='])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    instructions_show = 0
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
            sections_customized = 1
            if arg == 'all':
                all_section = 1
            else:
                sections_name = split_section_name_from_sections_part(arg)
                if sections_name == None:
                    print "Section '%s' is not supported" % (arg)
                    sys.exit(3)
        elif opt in ('-a'):
            sections_customized = 1
            sections_name_addition = split_section_name_from_sections_part(arg)
            if sections_name_addition == None:
                print "ERROR! Section '%s' is not supported" % (arg)
                sys.exit(3)
        elif opt in ('-d'):
            sections_customized = 1
            sections_name_removed = split_section_name_from_sections_part(arg)
            if sections_name_removed == None:
                print "Section '%s' is not supported" % (arg)
                sys.exit(3)
        elif opt in ('-o'):
            output_type = output_type_file
            output_file_name = arg
        elif opt in ('-D'):
            output_file_by_day = 1
        elif opt in ('-e'):
            errlog_file_name = arg
        elif opt in ('-i'):
            status_collect_interval = int(arg)
        elif opt in ('-n'):
            status_collect_times = int(arg)
        elif opt in ('-S'):
            speed_calculate_by_remote_monitor_system = 1
        elif opt in ('--socket'):
            socket_file = arg
        elif opt in ('--falcon'):
            import requests
            import json
            output_type = output_type_open_falcon
            open_falcon = arg
        elif opt in ('--net-face'):
            net_face_name = arg
        elif opt in ('--disk-name'):
            disk_name = arg
        elif opt in ('--proc-pid'):
            if arg.isdigit():
                proc_pid = int(arg)
            elif len(arg) > 0 and arg.startswith("file:"):
                pidfile_array = arg.split(':',2)
                if len(pidfile_array) != 2:
                    print 'ERROR! Pid file Option \'--proc-pid\' must be the process pid number or the exists pid file.'
                    sys.exit(3)

                proc_pidfile = pidfile_array[1]
                proc_pid = get_proc_pid_from_pid_file(proc_pidfile)
            else:
                print 'ERROR! Option \'--proc-pid\' must be the process pid number or the exists pid file.'
                print 'If option \'--proc-pid\' is pid file, it must be start with \'file:\'.'
                sys.exit(3)

            proc_pid_is_set = 1
        else:
            print 'ERROR! Unhandled option'
            sys.exit(3)

    server = None
    sections_to_show_default = []
    if (service_type == type_linux):
        server = Server("OS", service_type, None, None, None, [])
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
        elif len(sections_name) == 0:
            if output_type == output_type_screen or output_type == output_type_file:
                sections_to_show_default = common_sections_to_show_default
            else:
                sections_to_show_default = common_sections
                sections_to_show_default.append(proc_cpu_section)
                sections_to_show_default.append(proc_mem_section)
    elif (service_type == type_mysql):
        server = Server("Mysql", service_type,
                        mysql_initialize_for_server,
                        mysql_clean_for_server,
                        mysql_get_pidnum_for_server,
                        mysql_sections)
        server.check_alive = check_mysql_alive
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
            for section in mysql_sections:
                server.addSectionToShowByName(section.getName())
        elif (len(sections_name) == 0):
            if output_type == output_type_screen or output_type == output_type_file:
                sections_to_show_default = mysql_sections_to_show_default
            else:
                sections_to_show_default = mysql_sections
                sections_to_show_default.append(proc_cpu_section)
                sections_to_show_default.append(proc_mem_section)
    elif (service_type == type_redis):
        server = Server("Redis", service_type,
                        redis_initialize_for_server,
                        redis_clean_for_server,
                        redis_get_pidnum_for_server,
                        redis_sections)
        server.check_alive = check_redis_alive
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
            for section in redis_sections:
                server.addSectionToShowByName(section.getName())
        elif (len(sections_name) == 0):
            if output_type == output_type_screen or output_type == output_type_file:
                sections_to_show_default = redis_sections_to_show_default
            else:
                sections_to_show_default = redis_sections
                sections_to_show_default.append(proc_cpu_section)
                sections_to_show_default.append(proc_mem_section)
    elif (service_type == type_pika):
        server = Server("Pika", service_type,
                        pika_initialize_for_server,
                        pika_clean_for_server,
                        pika_get_pidnum_for_server,
                        pika_sections)
        server.check_alive = check_redis_alive    #Use the redis check alive function.
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
            for section in pika_sections:
                server.addSectionToShowByName(section.getName())
        elif (len(sections_name) == 0):
            if output_type == output_type_screen or output_type == output_type_file:
                sections_to_show_default = pika_sections_to_show_default
            else:
                sections_to_show_default = pika_sections
                sections_to_show_default.append(proc_cpu_section)
                sections_to_show_default.append(proc_mem_section)
    elif (service_type == type_memcached):
        server = Server("Memcached", service_type,
                        memcached_initialize_for_server,
                        memcached_clean_for_server,
                        memcached_get_pidnum_for_server,
                        memcached_sections)
        server.check_alive = check_memcached_alive
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
            for section in memcached_sections:
                server.addSectionToShowByName(section.getName())
        elif (len(sections_name) == 0):
            if output_type == output_type_screen or output_type == output_type_file:
                sections_to_show_default = memcached_sections_to_show_default
            else:
                sections_to_show_default = memcached_sections
                sections_to_show_default.append(proc_cpu_section)
                sections_to_show_default.append(proc_mem_section)
    elif (service_type == type_twemproxies):
        import json
        server = Server("Twemproxies", service_type,
                        twemproxies_initialize_for_server,
                        twemproxies_clean_for_server,
                        None,
                        twemproxies_sections)
        if all_section == 1:
            server.setDefaultSectionsToShow(common_sections)
            for section in twemproxies_sections:
                server.addSectionToShowByName(section.getName())
        elif (len(sections_name) == 0):
            if output_type == output_type_screen or output_type == output_type_file:
                sections_to_show_default = twemproxies_sections_to_show_default
            else:
                sections_to_show_default = twemproxies_sections
                sections_to_show_default.append(proc_cpu_section)
                sections_to_show_default.append(proc_mem_section)

    if (len(server.sections_to_show) == 0):
        server.setDefaultSectionsToShow(sections_to_show_default)

    for section_name in sections_name:
        if all_section == 1:
            break

        ret = server.addSectionToShowByName(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getType())
            print server.getType() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    for section_name in sections_name_addition:
        ret = server.addSectionToShowByName(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getType())
            print server.getType() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    for section_name in sections_name_removed:
        ret = server.removeSectionFromShowByName(section_name)
        if (ret < 0):
            print "Section '%s' is not supported for %s" % (section_name, server.getType())
            print server.getType() + " supported sections: " + server.getSupportedSectionsName()
            sys.exit(3)

    server.setTypeSectionsToShowIfNeeded()

    if (instructions_show == 1):
        print_sections_instructions(server)
        sys.exit(1)

    if output_type == output_type_file:
        output_file = open(output_file_name+'_'+current_day, 'a', 0)

    # Init the server if needed.
    if (server.initialize != None):
        try:
            server.initialize(server)
        except Exception, e:
            server.err = 1
            server.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e)

    if output_type == output_type_open_falcon:
        server.uploadToOpenFalcon()
    else:
        if speed_calculate_by_remote_monitor_system == 1:
            speed_calculate_by_remote_monitor_system = 0

        server.showStatus()

    # Clean the server if needed.
    if (server.clean != None):
        try:
            server.clean(server)
        except Exception, e:
            server.err = 1
            server.errmsg = get_exception_message(sys._getframe().f_code.co_name,sys._getframe().f_lineno, e)

    if (output_type == output_type_file and output_file.closed == False):
        output_file.close()