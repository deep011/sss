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
	
## Run
	
	$ python sss.py -T mysql -H ip -P port -u user -p password
			 --------------cmds--------------- -------net------- ------------connection------------ ------innodb------ 
		Time|  TPs   QPs  DPs  IPs  UPs  DIUPs|   NetIn   NetOut|  TryNewConns  AbortedConns  Conns|  IFSPs  IBPPDirty|
	12:10:49|   13    20    0    4    7     11|   20.1K   119.9K|            0             0    228|     17       1406|
	12:10:50|   27    39    0   42    1     43|   59.6K   254.8K|           86             0    228|     35       1530|
	12:10:51|    9     6    0   18    0     18|   28.4K    42.2K|           79             0    228|     16       1559|
	12:10:53|    4     4    0   12    0     12|   27.5K   106.7K|           63             0    228|      6       1590|
	12:10:54|    7     2    0   18    1     19|   15.2K   134.0K|           37             0    228|     12       1596|
	12:10:55|    4     7    0   12    0     12|   22.1K    71.7K|           68             0    228|     11       1580|
	12:10:56|    3     1    0    6    0      6|    7.8K    16.2K|           32             0    228|      8       1586|
	12:10:58|   13     1    0   28    0     28|   23.7K    75.3K|           32             0    228|     28       1624|
	
## Customization

Add the fields that you want to display into the 'status' dictionary, and use the 'StatusSection' and 'StatusColumn' class to display the columns.

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