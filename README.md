# sss

**sss** (abbreviation "Show-Service-Status") is a convenient tool to Show the Service Status(Now only support for os and mysql).

## Usage

    $ python sss.py -h
    python sss.py [options]

    options:
    -h,--help: show this help message
    -v,--version: show the version
    -H: target host
    -P: target port
    -u: target service user
    -p: target user password
    -T: target service type, default is os
    -s: sections to show, use comma to split
    -a: addition sections to show, use comma to split
    -d: removed sections for the showing, use comma to split
    -I,--instructions: show the support sections' instructions
    -o: output the status to this file
    -D: separate output files by day, suffix of the file name is '_yyyy-mm-dd'
    -i: interval time to show the status, unit is second
    --net-face: set the net device face name for os_net_* sections, default is 'lo'
    --disk-name: set the disk device name for os_disk sections, default is 'vda'
    --proc-pid: set the process pid number for proc_* sections, default is 0
    
## Run
    
Show the mysql service status, the follow is only the default sections to show, you can use -s,-a,-d options to customize the sections.
    
    $ python sss.py -T mysql -H ip -P port -u user -p password
    --time--- --------------cmds--------------- -------net------- -------------threads_conns-------------- 
         Time|  TPs   QPs  DPs  IPs  UPs  DIUPs|   NetIn   NetOut|  Run  Create  Cache  Conns   Try  Abort|
     22:24:19|   17    15    0   29    1     30|   39.2K   220.0K|    6       0      7    229    45      0|
     22:24:20|   22    33    0   34    3     37|   63.1K   271.7K|   13       0      7    229   147      0|
     22:24:21|   46    57    0   50    7     57|   82.6K   302.6K|    5       0      7    229   123      0|
     22:24:22|    8     3    0   16    1     17|   27.1K   120.1K|    4       0      7    229    61      0|
     22:24:23|   52     8    0   94    1     95|   44.4K   122.3K|    2       0      7    229    76      0|
     22:24:24|   39     4    0   79    0     79|   42.6K   113.5K|    5       0      7    229   111      0|
     22:24:25|   16     6    0   37    1     38|   25.2K   124.6K|    2       0      7    229    41      0|
     22:24:26|    9     5    0   17    1     18|   38.0K   183.6K|    4       0      7    229   126      0|
     
     
Show the os status, the follow is only the default sections to show, you can use -s,-a,-d options to customize the sections.
    
    $ python sss.py -T os --net-face=eth0 --disk-name=vdc
    --time--- -------os_cpu------- ------------------------os_disk------------------------ --os_net_bytes-- --os_swap--- 
         Time|  usr  sys  idl  iow|   Reads  Writes  RBytes  WBytes Queue Wait STime %util|      In     Out|    si    so|
     12:05:37| 14.3  9.4 74.3  1.9|    11.0   337.4   43.9K   30.8M   2.2  6.4   2.9  99.8|  391.3K  843.7K|     0     0|
     12:05:38| 13.7  8.7 75.8  1.8|    13.0   349.6   51.9K   27.8M   2.2  6.0   2.7  99.5|  417.7K  906.4K|     8     0|
     12:05:39| 12.7  7.5 75.6  4.3|     8.0   301.7   32.0K   29.1M   2.3  7.4   3.2  98.8|  319.1K  729.7K|     0     0|
     12:05:40| 13.8  8.2 77.1  0.9|    11.0   273.5   43.9K   22.4M   2.1  7.4   3.5  99.5|  330.9K  760.6K|     0     0|
     12:05:41| 13.5  8.7 76.1  1.6|    10.0   310.7   40.0K   25.4M   2.0  6.4   3.1  99.0|  388.5K  826.7K|     3     0|
     12:05:42| 13.9  8.0 76.9  1.1|     8.0   300.7   32.0K   26.8M   2.1  6.6   3.2  98.6|  330.5K  800.7K|     8     0|
     12:05:43| 13.2  8.3 77.3  1.3|     9.0   323.4   35.9K   31.2M   2.2  6.5   3.0  99.5|  321.9K  719.9K|     8     0|
     12:05:44|  9.8  6.5 82.8  0.9|    10.0   372.6   40.0K   33.5M   2.2  6.0   2.6  99.2|  354.8K  763.7K|     0     0|
     12:05:45| 16.7 10.4 71.8  1.1|     2.0   317.4    8.0K   29.2M   2.2  6.7   3.1  99.6|  295.5K  675.0K|     9     0|
     12:05:46| 12.2  8.6 78.1  1.1|     6.0   304.4   24.0K   29.4M   2.1  6.9   3.2  99.3|  308.7K  671.3K|    30     0|
    

## Customize the status sections

Support os status sections: 'time','os_cpu','os_load','os_swap','os_net_bytes','os_net_packages','os_disk','proc_cpu','proc_mem'

Support mysql status sections: 'time','os_cpu','os_load','os_swap','os_net_bytes','os_net_packages','os_disk','proc_cpu','proc_mem','cmds','net','threads_conns','innodb_redo_log','innodb_log','innodb_bp_usage','innodb_rows','innodb_data','row_lock','table_lock','innodb_internal_lock'


You can use -I option to show the sections instructions, the follow is the mysql sections:

    $ python sss.py -T mysql -I
	sss version 0.1.0
    * Use -T option to set the service type and show the type support sections' instructions
    
    Mysql status sections' instructions are as follows
    ________________________________________
    Section|time : os time
    ----------------------------------------
    Column |Time : show the time when the status display
    ________________________________________
    Section|os_cpu : os cpu status, collect from /proc/stat file
    ----------------------------------------
    Column |usr : percentage of cpu user+nice time
    Column |sys : percentage of cpu system+irq+softirq time
    Column |idl : percentage of cpu idle time
    Column |iow : percentage of cpu iowait time
    ________________________________________
    Section|os_load : os cpu average load status, collect from
           | /proc/loadavg file
    ----------------------------------------
    Column |1m : one minute average active tasks
    Column |5m : five minute average active tasks
    Column |15m : fifteen minute average active tasks
    ________________________________________
    Section|os_swap : os swap status, collect from /proc/vmstat file
    ----------------------------------------
    Column |si : counts per second of data moved from memory to swap,
           | related to pswpin
    Column |so : counts per second of data moved from swap to memory,
           | related to pswpout
    ________________________________________
    Section|os_net_bytes : os network bytes status, collect from
           | /proc/net/dev file, you need to use --net-face option to
           | set the net face name that you want to monitor, the net
           | face name is in the /proc/net/dev file
    ----------------------------------------
    Column |in : bytes per second the network incoming
    Column |out : bytes per second the network outgoing
    ________________________________________
    Section|os_net_packages : os network packages status, collect from
           | /proc/net/dev file, you need to use --net-face option to
           | set the net face name that you want to monitor, the net
           | face name is in the /proc/net/dev file
    ----------------------------------------
    Column |in : packages per second the network incoming
    Column |out : packages per second the network outgoing
    ________________________________________
    Section|os_disk : os disk status, collect from /proc/diskstats file,
           | you need to use --disk-name option to set the disk name
           | that you want to monitor, the disk name is in the
           | /proc/diskstats file
    ----------------------------------------
    Column |reads : counts per second read from the disk
    Column |writes : counts per second write to the disk
    Column |rbytes : bytes per second read from the disk
    Column |wbytes : bytes per second write to the disk
    Column |queue : disk queue length per second
    Column |await : average milliseconds of queue and service time for
           | each read/write
    Column |svctm : average milliseconds of service time for each
           | read/write
    Column |%util : disk utilization percent
    ________________________________________
    Section|proc_cpu : process cpu status, collect from /proc/[pid]/stat
           | file, usually the pid should automatically get from the
           | server.getPidNum() function, but you can also replace the
           | pid by the --proc-pid option
    ----------------------------------------
    Column |%cpu : cpu utilization per second
    ________________________________________
    Section|proc_mem : process memory status, collect from
           | /proc/[pid]/status file, usually the pid should
           | automatically get from the server.getPidNum() function, but
           | you can also replace the pid by the --proc-pid option
    ----------------------------------------
    Column |rss : bytes for resident memory size of the process in
    Column |vsz : bytes for virtual memory size of the process in
    ________________________________________
    Section|cmds : mysql commands status, collect from 'show global
           | status'
    ----------------------------------------
    Column |TPs : transactions per second
    Column |QPs : select commands per second
    Column |DPs : delete commands per second
    Column |IPs : insert commands per second
    Column |UPs : update commands per second
    Column |DIUPs : ddl(delete+insert+update) commands per second
    ________________________________________
    Section|net : mysql network status, collect from 'show global
           | status'
    ----------------------------------------
    Column |NetIn : bytes per second received from all clients
    Column |NetOut : bytes per second sent to all clients
    ________________________________________
    Section|threads_conns : mysql thread status, collect from 'show
           | global status'
    ----------------------------------------
    Column |Run : the number of threads that are not sleeping
    Column |Create : counts per second of threads created to handle
           | connections
    Column |Cache : the number of threads in the thread cache
    Column |Conns : the number of currently open connections
    Column |Try : counts per second of connection attempts (successful
           | or not) to the MySQL server
    Column |Abort : counts per second of failed attempts to connect to
           | the MySQL server
    ________________________________________
    Section|innodb_redo_log : mysql innodb redo log status, collect from
           | 'show engine innodb status'
    ----------------------------------------
    Column |Written : bytes per second redo log data written
    Column |Flushed : bytes per second redo log data flushed
    Column |Checked : bytes per second redo log data checked
    ________________________________________
    Section|innodb_log : mysql innodb redo log status, collect from
           | 'show global status' and 'show engine innodb status'
    ----------------------------------------
    Column |HisList : history list length
    Column |Fsyncs : counts per second of fsync() writes done to the log
           | file
    Column |Written : bytes per second written to the log file
    ________________________________________
    Section|innodb_bp_usage : mysql innodb buffer pool status, collect
           | from 'show global status'
    ----------------------------------------
    Column |DataPct : data pages percentage of possession in total pages
    Column |Dirty : the number of pages currently dirty
    Column |DReads : counts per second of logical reads that InnoDB
           | could not satisfy from the buffer pool, and had to read
           | directly from the disk
    Column |Reads : counts per second of logical read requests
    Column |Writes : counts per second of writes done to the InnoDB
           | buffer pool
    ________________________________________
    Section|innodb_rows : mysql innodb rows status, collect from 'show
           | global status'
    ----------------------------------------
    Column |Insert : counts per second of rows inserted into InnoDB
           | tables
    Column |Update : counts per second of rows updated in InnoDB tables
    Column |Delete : counts per second of rows deleted in InnoDB tables
    Column |Read : counts per second of rows read from InnoDB tables
    ________________________________________
    Section|innodb_data : mysql innodb data status, collect from 'show
           | global status'
    ----------------------------------------
    Column |Reads : counts per second of data reads (OS file reads)
    Column |Writes : counts per second of data writes
    Column |Read : bytes per second data read
    Column |Written : bytes per second data written
    ________________________________________
    Section|row_lock : mysql row lock status, collect from 'show global
           | status'
    ----------------------------------------
    Column |LWaits : times per second a row lock had to be waited for
    Column |LTime : milliseconds spent in acquiring row locks among one
           | second
    ________________________________________
    Section|table_lock : mysql table lock status, collect from 'show
           | global status'
    ----------------------------------------
    Column |LWait : times per second that a request for a table lock
           | could not be granted immediately and a wait was needed. If
           | this is high and you have performance problems, you should
           | first optimize your queries, and then either split your
           | table or tables or use replication
    Column |LImt : times per second that a request for a table lock
           | could be granted immediately
    ________________________________________
    Section|innodb_internal_lock : mysql innodb internal lock status,
           | collect from 'show engine innodb status'
    ----------------------------------------
    Column |MSpin : times per second the Mutex spin waits
    Column |MRound : times per second the threads looped in the
           | spin-wait cycle for Mutex
    Column |MOWait : times per second the thread gave up spin-waiting
           | and went to sleep instead for Mutex
    Column |SSpin : times per second the RW-shared spin waits
    Column |SRound : times per second the threads looped in the
           | spin-wait cycle for RW-shared
    Column |SOWait : times per second the thread gave up spin-waiting
           | and went to sleep instead for RW-shared
    Column |ESpin : times per second the RW-excl spin waits
    Column |ERound : times per second the threads looped in the
           | spin-wait cycle for RW-excl
    Column |EOWait : times per second the thread gave up spin-waiting
           | and went to sleep instead for RW-excl
    ________________________________________

    
## Customize sss development

sss is a Modular and Customized Design. You can easy to customize and support any other service status to show.

Add the fields that you want to display into the 'status' dictionary in the Server class, and use the 'StatusSection' and 'StatusColumn' class to display the columns.

The 'StatusSection' and 'StatusColumn' are used like the follow:

```python   
mysql_commands_section = StatusSection("cmds", [
StatusColumn("TPs", 0, column_flags_rate, field_handler_common, ["Com_commit", "Com_rollback"]),
StatusColumn("QPs", 3, column_flags_rate, field_handler_common, ["Com_select"]),
StatusColumn("DPs", 0, column_flags_rate, field_handler_common,["Com_delete"]),
StatusColumn("IPs", 0, column_flags_rate, field_handler_common,["Com_insert"]),
StatusColumn("UPs", 0, column_flags_rate, field_handler_common,["Com_update"]),
StatusColumn("DIUPs", 0, column_flags_rate, field_handler_common,["Com_delete","Com_insert","Com_update"])
], [get_mysql_status])
```

If you want sss to support other service, please implement the Server class like the mysql.