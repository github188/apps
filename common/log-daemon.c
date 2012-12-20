#include <stdio.h>
#include <stdlib.h>
#include <sqlite3.h>
#include <syslog.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdio.h>
#include <error.h>
#include <time.h>
#include <stdint.h>
#include "log.h"

#define ERROR_QUIT() kill(getpid(), SIGUSR1)

int sock_fd = -1;
static unsigned long long error_counter = 0;

void daemon_release()
{
	closelog();
	if (sock_fd)
		close(sock_fd);
	exit(-1);
}

void sig_int(int signo)
{
	syslog(LOG_ERR, "recv SIGINT daemon quit!");
	daemon_release();
}

void sig_usr(int signo)
{
	syslog(LOG_ERR, "daemon terminated by user! recvfrom() retcode %llu error!", error_counter);
	daemon_release();
}

int log_daemon()
{
	// for socket
        struct sockaddr_un local_addr;
        size_t addr_len;

	// for db
	sqlite3 *db_handle;

	signal(SIGINT, sig_int);
	signal(SIGQUIT, sig_int);
	signal(SIGTERM, sig_int);
	signal(SIGUSR1, sig_usr);

	openlog("DBLOG", LOG_NDELAY|LOG_PID, LOG_USER);

	// 检查数据库是否存在，存在打开，否则创建
	if ( !log_db_exist() && !log_db_create())
	{
		syslog(LOG_ERR, "create log database error!");
		ERROR_QUIT();
	}

	// open db
	if (SQLITE_OK != sqlite3_open(LOG_FILE, &db_handle))
	{
		syslog(LOG_ERR, "open db file error!");
		ERROR_QUIT();
	}

        // create socket fd
        if ((sock_fd=socket(AF_UNIX, SOCK_DGRAM, 0)) < 0)
	{
		syslog(LOG_ERR, "fail to create socket fd!");
		ERROR_QUIT();
	}

        // set local address
        local_addr.sun_family = AF_UNIX;
        strcpy(local_addr.sun_path, LOCAL_ADDR);
        unlink(local_addr.sun_path);
        addr_len = strlen(local_addr.sun_path) + sizeof(local_addr.sun_family);

        if (bind(sock_fd, (struct sockaddr*)&local_addr, addr_len) < 0)
        {
		syslog(LOG_ERR, "bind error!");
                close(sock_fd);
		ERROR_QUIT();
        }

	syslog(LOG_INFO, "started log daemon, waiting messge now...");

        // process message
        for (;;)
        {
#define MSG_MAX 900
#define CMD_MAX (MSG_MAX+100)
                ssize_t n;
                char mesg[MSG_MAX], sql_cmd[CMD_MAX];
		msg_request_t *msg;
		char *errmsg;

                n = recvfrom(sock_fd, mesg, MSG_MAX, 0, NULL, 0);
		if (n<=0)
		{
			error_counter++;
			if (error_counter >= 100)
				syslog(LOG_ERR, "recvfrom() has return code for %llu times!", error_counter);
			continue;
		}

		// check message header
		msg = (msg_request_t*)mesg;
		if (!MSG_HEADER_CORRECT(msg))
		{
			syslog(LOG_ERR, "msg header incorrcet!");
			continue;
		}

		/* CREATE TABLE jwlog(ID integer primary key autoincrement, date char(20), user char(32) null, module char(20), category char(20), event char(20), content varchar(2048)); */
		if (msg->user[0] == '\0')
			sprintf(msg->user, "INTERNAL");
		sprintf(sql_cmd, "INSERT INTO %s(date, user, module, category, event, content) VALUES(datetime('now','localtime'), '%s', '%s', '%s', '%s', '%s');", LOG_TABLE,
					msg->user, LogModuleStr(msg->module), LogCategoryStr(msg->category), LogEventStr(msg->event), msg->content);
		if (SQLITE_OK != sqlite3_exec(db_handle, sql_cmd, NULL, NULL, &errmsg))
			syslog(LOG_ERR, "insert error: %s\n", errmsg);
        }
	return -1;
}

int main()
{
	return log_daemon();
}
