#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>
#include <limits.h>
#include <sys/param.h>
#include <time.h>
#include "sys-global.h"
#include "../../common/jw-unistd.h"

#define TMPFS_MSG_ROOT "/tmp/.sys-mon/message"
#define _SORTED_ROOT TMPFS_MSG_ROOT"/sorted-all/"

#define DIRPTR _ptr
#define STAT _stat
#define _DIR_LIST_BEGIN(dir) \
do {						\
	DIR *_dir;				\
	struct dirent *_ptr;			\
	struct stat _stat;			\
	char _file[PATH_MAX];			\
	if ((_dir=opendir(dir)))		\
	{					\
		while((_ptr=readdir(_dir)))	\
		{				\
			sprintf(_file, "%s%s", dir, DIRPTR->d_name); \
			if (lstat(_file, &_stat)) \
				continue;

#define _DIR_LIST_END \
		}				\
		closedir(_dir);			\
	}					\
} while(0);


// 获取指定级别告警信息目录下记录条目数量
int tmpfs_msg_count(const char *level)
{
	char msg_dir[PATH_MAX];
	int _count = 0;

	if (level)
	{
		sprintf(msg_dir, "%s/%s/", TMPFS_MSG_ROOT, level);

		_DIR_LIST_BEGIN(msg_dir)
		{
			if (!S_ISREG(STAT.st_mode) && !S_ISLNK(STAT.st_mode))
				continue;
			_count++;
		}
		_DIR_LIST_END
	}
	return _count;
}

int _dir_max_file_num(const char *dir_path)
{
	int max = -1;

	_DIR_LIST_BEGIN(dir_path)
	{
		if (!S_ISREG(STAT.st_mode) && !S_ISLNK(STAT.st_mode))
			continue;
		if (atoi(DIRPTR->d_name) > max)
			max = atoi(DIRPTR->d_name);
	}
	_DIR_LIST_END
	return (max+1);
}

// 在指定告警级别目录下加入一条新信息，并且返回全路径文件名称
const char *tmpfs_msg_insert(const char *level, const char *msg)
{
	char msg_dir[PATH_MAX], msg_content[1024];
	static char msg_file[PATH_MAX];
	int fd;

	sprintf(msg_dir, "%s/%s/", TMPFS_MSG_ROOT, level);
	if (!mkdir_p(msg_dir))
	{
		return NULL;
	}

	sprintf(msg_file, "%s%d", msg_dir, _dir_max_file_num(msg_dir));
	if ( (fd=open(msg_file, O_CREAT|O_RDWR|O_TRUNC, S_IRWXU)) > 0 )
	{
		time_t t = time(NULL);
		sprintf(msg_content, "%s%s", ctime(&t), msg);
		*(strchr(msg_content, '\n')) = '|';
		write(fd, msg_content, strlen(msg_content));
		close(fd);
		return msg_file;
	}

	return NULL;
}

// 删除指定告警级别目录下创建时间最旧的一个文件，并且返回删除的全路径文件名称
const char *tmpfs_msg_remove_oldest(const char *level)
{
	time_t oldest; bool o_set = false;
	char msg_dir[PATH_MAX];
	static char oldest_file[PATH_MAX] = {0};

	sprintf(msg_dir, "%s/%s/", TMPFS_MSG_ROOT, level);
	_DIR_LIST_BEGIN(msg_dir)
	{
		if (!S_ISREG(STAT.st_mode) && !S_ISLNK(STAT.st_mode))
			continue;

		if (!o_set)
		{
			oldest = STAT.st_mtime;
			o_set = true;
		}

		if (STAT.st_mtime <= oldest)
		{
			sprintf(oldest_file, "%s%s", msg_dir, DIRPTR->d_name);
			oldest = STAT.st_mtime;
		}
	}
	_DIR_LIST_END

	if ( (oldest_file[0]!='\0') && !unlink(oldest_file) )
	{
		return oldest_file;
	}
	return NULL;
}

// 链接全局告警信息
ssize_t tmpfs_msg_sorted_link(const char *file)
{
	char link[PATH_MAX];

	if (file && mkdir_p(_SORTED_ROOT))
	{
		sprintf(link, "%s%d", _SORTED_ROOT, _dir_max_file_num(_SORTED_ROOT));
		return symlink(file, link);
	}
	return -1;
}

// 删除指定全局告警信息
ssize_t tmpfs_msg_sorted_unlink(const char *file)
{
	ssize_t ret = -1;

	if (!file)
		return ret;

	_DIR_LIST_BEGIN(_SORTED_ROOT)
	{
		if (!S_ISLNK(STAT.st_mode))
			continue;

		char _link[PATH_MAX], _file[PATH_MAX];
		ssize_t _sz;

		sprintf(_link, "%s%s", _SORTED_ROOT, DIRPTR->d_name);
		if ( (_sz=readlink(_link, _file, sizeof(_file))) > 0)
		{
			_file[_sz] = '\0';
			if (!strcmp(file, _file))
			{
				ret = unlink(_link);
				break;
			}
		}
	}
	_DIR_LIST_END
	return ret;
}
