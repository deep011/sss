### 0.1.0 - Jan 17, 2017

This is the sss first release. sss is used to show a service status, and it is developed in template. User can easily support the service, monitor sections and columns.

* Support show the OS status, such as 'time','os_cpu','os_load','os_swap','os_net_bytes','os_net_packages','os_disk','proc_cpu','proc_mem'. (deep011)
* Support show the Mysql status, such as 'cmds','net','threads_conns','innodb_redo_log','innodb_log','innodb_bp_usage','innodb_rows','innodb_data','row_lock','table_lock','innodb_internal_lock','slave','handler_read','handler_ddl','handler_trx'. (deep011)
* Support output the status to files(use the option -o). (deep011)
* Support separate output files by day(use the option -D). (deep011)
* Support customize the displayed sections(use the options -s,-a,-d). (deep011)
