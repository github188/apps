#include "sys-global.h"

#define TMPFS_MSG_ROOT "/tmp/.sys-mon/message"
#define _SORTED_ROOT TMPFS_MSG_ROOT"/sorted-all"

/*extern*/ sys_global_t gconf;

void sys_global_init()
{
	gconf.tmpfs = false;
	gconf.info_size = 10;
	gconf.warning_size = 10;
	gconf.error_size = 10;
}

bool _path_exist(const char *path)
{
}

// 获取指定级别告警信息目录下记录条目数量
int tmpfs_msg_count(const char *level)
{
	char msg_dir[PATH_MAX];

	if (!level)
		return 0;

	sprintf(msg_dir, "%s/%s", TMPFS_MSG_ROOT, level);
	if (!_path_exist(msg_dir))
		return 0;
}

// 在指定告警级别目录下加入一条新信息，并且返回全路径文件名称
const char *tmpfs_msg_insert(const char *level, const char *msg)
{
}

// 删除指定告警级别目录下创建时间最旧的一个文件，并且返回删除的全路径文件名称
const char *tmpfs_msg_remove_oldest(const char *level)
{
}

// 链接全局告警信息
ssize_t tmpfs_msg_sorted_link(const char *file)
{
}

// 删除指定全局告警信息
ssize_t tmpfs_msg_sorted_unline(const char *file)
{
}

void dump_sys_global()
{
	puts("--------- global ---------");
	if (gconf.tmpfs)
		puts("tmpfs: true");
	else
		puts("tmpfs: false");
	puts("msg_buff_size:");
	printf("  info: %d\n", gconf.info_size);
	printf("  warning: %d\n", gconf.warning_size);
	printf("  error: %d\n", gconf.error_size);
}
