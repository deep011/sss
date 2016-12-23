# sss

**sss** is a convenient tool to show the service status(Now only support for mysql).

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
    -T: target service type, default is mysql
    -s: sections to show, use comma to split
    -a: addition sections to show, use comma to split
    -d: removed sections for the showing, use comma to split
    
## Run
    
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
    
## Customization

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
])
```

If you want sss to support other service, please implement the Server class like the mysql.