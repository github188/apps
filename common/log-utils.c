#include <unistd.h>
#include <sqlite3.h>
#include <stdio.h>
#include "log.h"

const char *_mod_name[] = {"Web", "Disk", "VG", "UDV", "iSCSI", "NAS", "SysConf", "Unknown", NULL};
const char *_mod_category[] = {"Auto", "Manual", NULL};
const char *_mod_event[] = {"Info", "Warning", "Error", NULL};

/* 检查日志文件是否存在
 *   存在条件:
 *   1. 文件存在
 *   2. 文件有读写权限
 *   3. 是sqlite数据库文件
 */
bool log_db_exist()
{
	sqlite3 *tmp_handle;
	char *errmsg;
	int col, row;
	char **result;

	if (access(LOG_FILE, F_OK))
		return false;
	if (access(LOG_FILE, R_OK|W_OK))
		return false;
	if (SQLITE_OK != sqlite3_open_v2(LOG_FILE, &tmp_handle, SQLITE_OPEN_READONLY, NULL))
		return false;
	if (sqlite3_get_table(tmp_handle, "select count(*) from jwlog", &result, &col, &row, &errmsg))
		return false;
	sqlite3_free_table(result);
	sqlite3_close(tmp_handle);
	return true;
}

bool log_db_create()
{
	sqlite3 *tmp_handle;
	char *errmsg;
	char sql_cmd[1024];
	bool retcode = false;

	if (SQLITE_OK != sqlite3_open(LOG_FILE, &tmp_handle))
		return false;

	sprintf(sql_cmd, "CREATE TABLE %s(ID integer primary key autoincrement, date datetime, module char(20), category char(20), event char(20), content varchar(2048));", LOG_TABLE);
	if (SQLITE_OK == sqlite3_exec(tmp_handle, sql_cmd, NULL, NULL, &errmsg))
		retcode = true;
	sqlite3_close(tmp_handle);

	return retcode;
}

