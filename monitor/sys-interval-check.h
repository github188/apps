#include "sys-global.h"
#include "list.h"

#ifndef _SYS_INTERVAL_CHECK_
#define _SYS_INTERVAL_CHECK_

#define VAL_IGNORE -1
#define VAL_INVALID 0
#define isValid(val) ( ((val)!=VAL_IGNORE) && ((val)!=VAL_INVALID) )

#define isExecutable(item) (item->_capture)
#define isExpried(item) ((int)difftime(time(NULL), item->_last_update) >= item->check_intval)
#define update(item) item->_last_update = time(NULL)
#define execute(item) item->_capture()

#define CHECK_INTVAL 5

/// callback
typedef int (*capture_func)(char *msg_out);

bool isCaptureSupported(const char *mod);
capture_func capture_get(const char *mod);

typedef struct _sys_capture_conf sys_capture_t;
struct _sys_capture_conf {
	struct list list;
	char name[64];
	int check_intval;
	int min_thr, max_thr;
	time_t _last_update;		// 最后更新时间
	capture_func _capture;		// 获取系统信息的函数
	bool _error;			// true - 获取的值出错, false - 出错事件解除
	bool _preset;			// 是否使用预先设置的值检查
};

extern struct list _g_capture;

void sys_capture_init();
sys_capture_t *sys_capture_alloc();
void sys_capture_set_handler(sys_capture_t *cap);
void sys_capture_add(sys_capture_t *cap);

void do_interval_check(int sig);

void dump_self_run();

#endif/*_SYS_INTERVAL_CHECK_*/
