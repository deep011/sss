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