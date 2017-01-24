# sss

**sss** (abbreviation "Show-Service-Status") is a convenient tool to Show the Service Status.

By now, sss support for os(linux), mysql, redis and memcached.

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
    
## Dependence

Mysql need [mysql-connector-python](https://dev.mysql.com/downloads/connector/python/)

Redis need [redis-py](https://github.com/andymccurdy/redis-py)

Memcached need [python-memcached](https://github.com/linsomniac/python-memcached)


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
    
The unit displayed in two ways: [k,m,g,t] and [K,M,G,T].

Unit [k,m,g,t] means it is number. 1t=1000g 1g=1000m 1m=1000k 1k=1000

Unit [K,M,G,T] means it is bytes. 1T=1024G 1G=1024M 1M=1024K 1K=1024bytes

## Customize the status sections

Support os status sections: 'time','os_cpu','os_load','os_swap','os_net_bytes','os_net_packages','os_disk','os_mem','proc_cpu','proc_mem'

Support mysql status sections: 'time','os_cpu','os_load','os_swap','os_net_bytes','os_net_packages','os_disk','os_mem','proc_cpu','proc_mem','cmds','net','threads_conns','innodb_redo_log','innodb_log','innodb_bp_usage','innodb_rows','innodb_data','row_lock','table_lock','innodb_internal_lock','slave','handler_read','handler_ddl','handler_trx'

Support redis status sections: 'time','os_cpu','os_load','os_swap','os_net_bytes','os_net_packages','os_disk','os_mem','proc_cpu','proc_mem','connection','client','mem','net','keyspace','key','command','persis','repl'

### You can use -I option to show the sections instructions, the follow is the mysql sections:

    $ python sss.py -T mysql -I
	sss version 0.1.1
    * Use -T option to set the service type and show the type support sections' instructions
    
    Mysql status sections' instructions are as follows
    ________________________________________
    Section|time : os time
    ----------------------------------------
    Column |Time : Show the time when the status display.
    ________________________________________
    Section|os_cpu : os cpu status, collect from /proc/stat file
    ----------------------------------------
    Column |usr : Percentage of cpu user+nice time.
    Column |sys : Percentage of cpu system+irq+softirq time.
    Column |idl : Percentage of cpu idle time.
    Column |iow : Percentage of cpu iowait time.
    ________________________________________
    Section|os_load : os cpu average load status, collect from
           | /proc/loadavg file
    ----------------------------------------
    Column |1m : One minute average active tasks.
    Column |5m : Five minute average active tasks.
    Column |15m : Fifteen minute average active tasks.
    ________________________________________
    Section|os_swap : os swap status, collect from /proc/vmstat file
    ----------------------------------------
    Column |si : Counts per second of data moved from memory to swap,
           | related to pswpin.
    Column |so : Counts per second of data moved from swap to memory,
           | related to pswpout.
    ________________________________________
    Section|os_net_bytes : os network bytes status, collect from
           | /proc/net/dev file, you need to use --net-face option to
           | set the net face name that you want to monitor, the net
           | face name is in the /proc/net/dev file
    ----------------------------------------
    Column |in : Bytes per second the network incoming.
    Column |out : Bytes per second the network outgoing.
    ________________________________________
    Section|os_net_packages : os network packages status, collect from
           | /proc/net/dev file, you need to use --net-face option to
           | set the net face name that you want to monitor, the net
           | face name is in the /proc/net/dev file
    ----------------------------------------
    Column |in : Packages per second the network incoming.
    Column |out : Packages per second the network outgoing.
    ________________________________________
    Section|os_disk : os disk status, collect from /proc/diskstats file,
           | you need to use --disk-name option to set the disk name
           | that you want to monitor, the disk name is in the
           | /proc/diskstats file
    ----------------------------------------
    Column |reads : Counts per second read from the disk.
    Column |writes : Counts per second write to the disk.
    Column |rbytes : Bytes per second read from the disk.
    Column |wbytes : Bytes per second write to the disk.
    Column |queue : Disk queue length per second.
    Column |await : Average milliseconds of queue and service time for
           | each read/write.
    Column |svctm : Average milliseconds of service time for each
           | read/write.
    Column |%util : Disk utilization percent.
    ________________________________________
    Section|os_mem : os memory status, collect from /proc/meminfo file
    ----------------------------------------
    Column |total : Total memory size bytes.
    Column |free : Free memory size bytes.
    Column |buffer : Buffered memory size bytes.
    Column |cached : Cached memory size bytes.
    ________________________________________
    Section|proc_cpu : process cpu status, collect from /proc/[pid]/stat
           | file, usually the pid should automatically get from the
           | server.getPidNum() function, but you can also replace the
           | pid by the --proc-pid option
    ----------------------------------------
    Column |%cpu : Cpu utilization per second.
    ________________________________________
    Section|proc_mem : process memory status, collect from
           | /proc/[pid]/status file, usually the pid should
           | automatically get from the server.getPidNum() function, but
           | you can also replace the pid by the --proc-pid option
    ----------------------------------------
    Column |rss : Bytes for resident memory size of the process in.
    Column |vsz : Bytes for virtual memory size of the process in.
    ________________________________________
    Section|cmds : mysql commands status, collect from 'show global
           | status'
    ----------------------------------------
    Column |TPs : Transactions per second.
    Column |QPs : Select commands per second.
    Column |DPs : Delete commands per second.
    Column |IPs : Insert commands per second.
    Column |UPs : Update commands per second.
    Column |DIUPs : DDL(delete+insert+update) commands per second.
    ________________________________________
    Section|net : mysql network status, collect from 'show global
           | status'
    ----------------------------------------
    Column |NetIn : Bytes per second received from all clients.
    Column |NetOut : Bytes per second sent to all clients.
    ________________________________________
    Section|threads_conns : mysql thread status, collect from 'show
           | global status'
    ----------------------------------------
    Column |Run : The number of threads that are not sleeping.
    Column |Create : Counts per second of threads created to handle
           | connections.
    Column |Cache : The number of threads in the thread cache.
    Column |Conns : The number of currently open connections.
    Column |Try : Counts per second of connection attempts (successful
           | or not) to the MySQL server.
    Column |Abort : Counts per second of failed attempts to connect to
           | the MySQL server.
    ________________________________________
    Section|innodb_redo_log : mysql innodb redo log status, collect from
           | 'show engine innodb status'
    ----------------------------------------
    Column |Written : Bytes per second redo log data written.
    Column |Flushed : Bytes per second redo log data flushed.
    Column |Checked : Bytes per second redo log data checked.
    ________________________________________
    Section|innodb_log : mysql innodb redo log status, collect from
           | 'show global status' and 'show engine innodb status'
    ----------------------------------------
    Column |HisList : History list length.
    Column |Fsyncs : Counts per second of fsync() writes done to the log
           | file.
    Column |Written : Bytes per second written to the log file.
    ________________________________________
    Section|innodb_bp_usage : mysql innodb buffer pool status, collect
           | from 'show global status'
    ----------------------------------------
    Column |DataPct : Data pages percentage of possession in total
           | pages.
    Column |Dirty : The number of pages currently dirty.
    Column |DReads : Counts per second of logical reads that InnoDB
           | could not satisfy from the buffer pool, and had to read
           | directly from the disk.
    Column |Reads : Counts per second of logical read requests.
    Column |Writes : Counts per second of writes done to the InnoDB
           | buffer pool.
    ________________________________________
    Section|innodb_rows : mysql innodb rows status, collect from 'show
           | global status'
    ----------------------------------------
    Column |Insert : Counts per second of rows inserted into InnoDB
           | tables.
    Column |Update : Counts per second of rows updated in InnoDB tables.
    Column |Delete : Counts per second of rows deleted in InnoDB tables.
    Column |Read : Counts per second of rows read from InnoDB tables.
    ________________________________________
    Section|innodb_data : mysql innodb data status, collect from 'show
           | global status'
    ----------------------------------------
    Column |Reads : Counts per second of data reads (OS file reads).
    Column |Writes : Counts per second of data writes.
    Column |Read : Bytes per second data read.
    Column |Written : Bytes per second data written.
    ________________________________________
    Section|row_lock : mysql row lock status, collect from 'show global
           | status'
    ----------------------------------------
    Column |LWaits : Times per second a row lock had to be waited for.
    Column |LTime : Milliseconds spent in acquiring row locks among one
           | second.
    ________________________________________
    Section|table_lock : mysql table lock status, collect from 'show
           | global status'
    ----------------------------------------
    Column |LWait : Times per second that a request for a table lock
           | could not be granted immediately and a wait was needed. If
           | this is high and you have performance problems, you should
           | first optimize your queries, and then either split your
           | table or tables or use replication.
    Column |LImt : Times per second that a request for a table lock
           | could be granted immediately.
    ________________________________________
    Section|innodb_internal_lock : mysql innodb internal lock status,
           | collect from 'show engine innodb status'
    ----------------------------------------
    Column |MSpin : Times per second the Mutex spin waits.
    Column |MRound : Times per second the threads looped in the
           | spin-wait cycle for Mutex.
    Column |MOWait : Times per second the thread gave up spin-waiting
           | and went to sleep instead for Mutex.
    Column |SSpin : Times per second the RW-shared spin waits.
    Column |SRound : Times per second the threads looped in the
           | spin-wait cycle for RW-shared.
    Column |SOWait : Times per second the thread gave up spin-waiting
           | and went to sleep instead for RW-shared.
    Column |ESpin : Times per second the RW-excl spin waits.
    Column |ERound : Times per second the threads looped in the
           | spin-wait cycle for RW-excl.
    Column |EOWait : Times per second the thread gave up spin-waiting
           | and went to sleep instead for RW-excl.
    ________________________________________
    Section|slave : mysql slave status, collect from 'show slave status'
    ----------------------------------------
    Column |Delay : This is the 'Seconds_Behind_Master', based on the
           | timestamps stored in events, measures the time difference
           | in seconds between the slave SQL thread and the slave I/O
           | thread. If the network connection between master and slave
           | is fast, the slave I/O thread is very close to the master,
           | so this field is a good approximation of how late the slave
           | SQL thread is compared to the master. If the network is
           | slow, this is not a good approximation; the slave SQL
           | thread may quite often be caught up with the slow-reading
           | slave I/O thread, so Seconds_Behind_Master often shows a
           | value of 0, even if the I/O thread is late compared to the
           | master. In other words, this column is useful only for fast
           | networks.
    Column |RSpace : The total combined size of all existing relay log
           | files.
    ________________________________________
	Section|handler_ddl : mysql handler ddl status, collect from 'show
           | global status'
    ----------------------------------------
    Column |Write : Requests per second to insert a row in a table.
    Column |Update : Requests per second to update a row in a table.
    Column |Del : Times per second that rows have been deleted from
           | tables
    ________________________________________
    Section|handler_trx : mysql handler transaction status, collect from
           | 'show global status'
    ----------------------------------------
    Column |Commit : Counts per second of internal COMMIT statements.
    Column |Pre : Counts per second of the prepare phase of two-phase
           | commit operations.
    Column |Rback : Requests per second for a storage engine to perform
           | a rollback operation.
    Column |Spoint : Requests per second for a storage engine to place a
           | savepoint.
    Column |SPRb : Requests per second for a storage engine to roll back
           | to a savepoint.
    ________________________________________
    
    
### The follow is the redis sections instructions:

    $ python sss.py -T redis -I
    sss version 0.1.1
    * Use -T option to set the service type and show the type support sections' instructions
    
    Redis status sections' instructions are as follows
    ________________________________________
    Section|time : os time
    ----------------------------------------
    Column |Time : Show the time when the status display.
    ________________________________________
    Section|os_cpu : os cpu status, collect from /proc/stat file
    ----------------------------------------
    Column |usr : Percentage of cpu user+nice time.
    Column |sys : Percentage of cpu system+irq+softirq time.
    Column |idl : Percentage of cpu idle time.
    Column |iow : Percentage of cpu iowait time.
    ________________________________________
    Section|os_load : os cpu average load status, collect from
           | /proc/loadavg file
    ----------------------------------------
    Column |1m : One minute average active tasks.
    Column |5m : Five minute average active tasks.
    Column |15m : Fifteen minute average active tasks.
    ________________________________________
    Section|os_swap : os swap status, collect from /proc/vmstat file
    ----------------------------------------
    Column |si : Counts per second of data moved from memory to swap,
           | related to pswpin.
    Column |so : Counts per second of data moved from swap to memory,
           | related to pswpout.
    ________________________________________
    Section|os_net_bytes : os network bytes status, collect from
           | /proc/net/dev file, you need to use --net-face option to
           | set the net face name that you want to monitor, the net
           | face name is in the /proc/net/dev file
    ----------------------------------------
    Column |in : Bytes per second the network incoming.
    Column |out : Bytes per second the network outgoing.
    ________________________________________
    Section|os_net_packages : os network packages status, collect from
           | /proc/net/dev file, you need to use --net-face option to
           | set the net face name that you want to monitor, the net
           | face name is in the /proc/net/dev file
    ----------------------------------------
    Column |in : Packages per second the network incoming.
    Column |out : Packages per second the network outgoing.
    ________________________________________
    Section|os_disk : os disk status, collect from /proc/diskstats file,
           | you need to use --disk-name option to set the disk name
           | that you want to monitor, the disk name is in the
           | /proc/diskstats file
    ----------------------------------------
    Column |reads : Counts per second read from the disk.
    Column |writes : Counts per second write to the disk.
    Column |rbytes : Bytes per second read from the disk.
    Column |wbytes : Bytes per second write to the disk.
    Column |queue : Disk queue length per second.
    Column |await : Average milliseconds of queue and service time for
           | each read/write.
    Column |svctm : Average milliseconds of service time for each
           | read/write.
    Column |%util : Disk utilization percent.
    ________________________________________
    Section|os_mem : os memory status, collect from /proc/meminfo file
    ----------------------------------------
    Column |total : Total memory size bytes.
    Column |free : Free memory size bytes.
    Column |buffer : Buffered memory size bytes.
    Column |cached : Cached memory size bytes.
    ________________________________________
    Section|proc_cpu : process cpu status, collect from /proc/[pid]/stat
           | file, usually the pid should automatically get from the
           | server.getPidNum() function, but you can also replace the
           | pid by the --proc-pid option
    ----------------------------------------
    Column |%cpu : Cpu utilization per second.
    ________________________________________
    Section|proc_mem : process memory status, collect from
           | /proc/[pid]/status file, usually the pid should
           | automatically get from the server.getPidNum() function, but
           | you can also replace the pid by the --proc-pid option
    ----------------------------------------
    Column |rss : Bytes for resident memory size of the process in.
    Column |vsz : Bytes for virtual memory size of the process in.
    ________________________________________
    Section|connection : redis connection status, collect from 'info'
    ----------------------------------------
    Column |conns : Counts for connected clients.
    Column |receive : Number of connections accepted by the server per
           | second.
    Column |reject : Number of connections rejected because of
           | maxclients limit per second.
    ________________________________________
    Section|client : redis client status, collect from 'info'
    ----------------------------------------
    Column |LOList : Longest client output list length.
    Column |BIBuf : Biggest client input buffer size in bytes.
    ________________________________________
    Section|mem : redis memory usage, collect from 'info'
    ----------------------------------------
    Column |used : Total number of bytes allocated by Redis using its
           | allocator (either standard libc, jemalloc, or an
           | alternative allocator such as tcmalloc.
    Column |rss : Number of bytes that Redis allocated as seen by the
           | operating system (a.k.a resident set size). This is the
           | number reported by tools such as top(1) and ps(1).
    Column |peak : Peak memory consumed by Redis (in bytes).
    ________________________________________
    Section|net : redis network status, collect from 'info'
    ----------------------------------------
    Column |in : Bytes per second received into redis.
    Column |out : Bytes per second sent by redis.
    ________________________________________
    Section|keyspace : redis keyspace status, collect from 'info'
    ----------------------------------------
    Column |keys : Number of keys in all db.
    Column |expires : Number of keys with an expiration in all db.
    ________________________________________
    Section|key : redis key status, collect from 'info'
    ----------------------------------------
    Column |hits : Count per second of successful lookup of keys in the
           | main dictionary.
    Column |misses : Count per second of failed lookup of keys in the
           | main dictionary.
    Column |expired : Number of key expiration events among one second.
    Column |evicted : Number of evicted keys due to maxmemory limit
           | among one second.
    ________________________________________
    Section|command : redis command status, collect from 'info
           | commandstat' and 'command'
    ----------------------------------------
    Column |cmds : Number of commands processed per second.
    Column |reads : Number of readonly commands processed per second.
    Column |writes : Number of write commands processed per second.
    ________________________________________
    Section|persis : redis persistence status, collect from 'info'
    ----------------------------------------
    Column |ln : Flag indicating if the load of a dump file is on-going.
    Column |rn : Flag indicating a RDB save is on-going.
    Column |an : Flag indicating a AOF rewrite operation is on-going.
    ________________________________________
    Section|repl : redis replication status, collect from 'info'
    ----------------------------------------
    Column |r : Value is 'M' if the instance is slave of no one(it is a
           | master), or 'S' if the instance is enslaved to a master(it
           | is a slave). Note that a slave can be master of another
           | slave (daisy chaining).
    Column |s/l : If the role is master, it means the number of
           | connected slaves. If the role is slave, it means the status
           | of the link (up/down)
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