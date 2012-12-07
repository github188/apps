#include <syslog.h>
#include <stdbool.h>
#include "list.h"
#include "../common/debug.h"
#include "../common/log.h"

#ifndef _SYS_MON_H_
#define _SYS_MON_H_

#define _LOG_OPT (LOG_CONS)
#define log_init() openlog("sys-mon", _LOG_OPT, LOG_DAEMON)
#define log_release() closelog()

#define VAL_IGNORE -1

#define isValid(val) (val != VAL_IGNORE)
#define isExecutable(item) (item->_capture)
#define isExpried(item) ((int)difftime(time(NULL), item->_last_update) >= item->check_int)
#define update(item) item->_last_update = time(NULL)
#define execute(item) item->_capture()

#define CHECK_INTVAL 5

extern struct list gconf;

/*---------------------------------------------------------------------------*/
/*   Alarm                                                                   */
/*---------------------------------------------------------------------------*/

/// Action
#define ALARM_BUZZER (1<<0)
#define ALARM_SYSLED (1<<1)
#define ALARM_EMAIL  (1<<2)

typedef struct _alarm_conf alarm_conf_t;
struct _alarm_conf {
	struct list list;
	char name[64];
	int action;
};

size_t mon_alarm_load();
size_t mon_alarm_reload();
void mon_alarm_release();
void raise_alarm(const char *module, const char *msg);

#define ALARM_CONF "/opt/sys/alarm-conf.xml"

/*---------------------------------------------------------------------------*/
/*   Capture                                                                 */
/*---------------------------------------------------------------------------*/

/// callback
typedef int (*capture_func)(void);

bool isCaptureSupported(const char *mod);
capture_func capture_get(const char *mod);

/*---------------------------------------------------------------------------*/
/*   Conf                                                                    */
/*---------------------------------------------------------------------------*/
typedef struct _mon_conf mon_conf_t;
struct _mon_conf {
	struct list list;
	char name[64];
	int check_int;
	int min_thr, max_thr;
	int min_alr, max_alr;
	time_t _last_update;	// 最后更新时间
	capture_func _capture;	// 获取系统信息的函数
};

size_t mon_conf_load();
size_t mon_conf_reload();
void mon_conf_release();

#define MON_CONF "/opt/sys/sys-mon-conf.xml"

#endif/*_SYS_MON_H_*/
