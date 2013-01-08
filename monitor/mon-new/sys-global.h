#include <stdbool.h>
#include <syslog.h>

#ifndef __SYS_GLOBAL_H__
#define __SYS_GLOBAL_H__

#define SYSMON_CONF "/opt/jw-conf/system/sysmon-conf.xml"
#define SYSMON_ADDR "/tmp/.sys-mon-socket-do-not-remove"

#define _LOG_OPT (LOG_CONS)
#define log_init() openlog("sys-mon", _LOG_OPT, LOG_DAEMON)
#define log_release() closelog()


typedef struct _sys_global sys_global_t;
struct _sys_global {
	bool tmpfs;
	struct {
		int info, warning, error;
	} msg_buff_size;
};
#define info_size msg_buff_size.info
#define warning_size msg_buff_size.warning
#define error_size msg_buff_size.error

extern sys_global_t gconf;

/*
 * tmpfs:
 *  /tmp/.sys-mon/message
 *                   |------/info/          记录info类型事件，上限sys_global.recent.info
 *                   |------/warning/       记录warning类型事件，上限sys_global.recent.warning
 *                   |------/error/         记录error类型事件，上限sys_global.recent.error
 *                   |------/sorted-all/    所有事件列表（链接）
 */

void sys_global_init();
void sys_mon_conf_check();
void sys_mon_load_conf();

int tmpfs_msg_count(const char *level);
const char *tmpfs_msg_insert(const char *level, const char *msg);
const char *tmpfs_msg_remove_oldest(const char *level);
ssize_t tmpfs_msg_sorted_link(const char *file);
ssize_t tmpfs_msg_sorted_unline(const char *file);

void dump_sys_global();

#endif/*__SYS_GLOBAL_H__*/
