#include <syslog.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdbool.h>
#include <signal.h>
#include "list.h"
#include "../common/debug.h"
#include "../common/log.h"

#ifndef _SYS_MON_H_
#define _SYS_MON_H_

#define _LOG_OPT (LOG_CONS)
#define log_init() openlog("sys-mon", _LOG_OPT, LOG_DAEMON)
#define log_release() closelog()

#define VAL_IGNORE -1
#define VAL_INVALID 0
#define isValid(val) ( ((val)!=VAL_IGNORE) && ((val)!=VAL_INVALID) )

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

#define ALARM_CONF "/opt/jw-conf/system/alarm-conf.xml"

#define ALARM_CONF_CONTENT "\
<?xml version=\"1.0\" encoding=\"UTF-8\"?><alarm> \
<category name=\"email\" switch=\"disable\"></category> \
<module buzzer=\"disable\" email=\"disable\" name=\"temperature\" switch=\"enable\" sys-led=\"enable\"/> \
</alarm> \
"

bool create_default_conf(const char *file, const char *content);
void write_alarm(const char *fname, const char *value);

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
	char _alarm_file[PATH_MAX]; // 告警文件通常存放在/tmp/jw/alarm/告警模块名称
};

size_t mon_conf_load();
size_t mon_conf_reload();
void mon_conf_release();

#define MON_CONF "/opt/jw-conf/system/mon-conf.xml"

#define MON_CONF_CONTENT "\
<?xml version=\"1.0\" encoding=\"UTF-8\"?> \
<mon> \
	<target name=\"cpu-temp\" check_interval=\"60\" min_threshold=\"ignore\" max_threshold=\"65\" min_alarm=\"ignore\" max_alarm=\"60\"/> \
	<target name=\"env-temp\" check_interval=\"60\" min_threshold=\"ignore\" max_threshold=\"65\" min_alarm=\"ignore\" max_alarm=\"60\"/> \
	<target name=\"case-temp\" check_interval=\"60\" min_threshold=\"ignore\" max_threshold=\"65\" min_alarm=\"ignore\" max_alarm=\"60\"/> \
	<target name=\"case-fan1\" check_interval=\"60\" min_threshold=\"1000\" max_threshold=\"ignore\" min_alarm=\"800\" max_alarm=\"ignore\"/> \
	<target name=\"case-fan2\" check_interval=\"60\" min_threshold=\"1000\" max_threshold=\"ignore\" min_alarm=\"800\" max_alarm=\"ignore\"/> \
	<target name=\"cpu-fan\" check_interval=\"60\" min_threshold=\"1000\" max_threshold=\"ignore\" min_alarm=\"800\" max_alarm=\"ignore\"/> \
</mon> \
"

#endif/*_SYS_MON_H_*/