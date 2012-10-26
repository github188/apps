#include <glob.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#include "util.h"
#include "dev_manage.h"
#include "md_super.h"
#include "pdm_info.h"

const char *dev_patterns[] = {
	"/dev/sd[a-z]",
	"/dev/sd[a-z][a-z]",
	"/dev/md[1-9]",
	"/dev/md[1-9][0-9]",
	NULL,
};

static struct md_dev *load_dev(const char *path)
{
	int fd;
	struct stat sts;
	struct super_type *st = NULL;
	pdm_super_t *pdm = NULL;
	struct md_dev *dev = NULL;

	fd = open(path, O_RDONLY | O_EXCL);
	if (fd < 0)
		return NULL;

	if (fstat(fd, &sts) < 0)
		goto failed;
	if ((sts.st_mode & S_IFMT) != S_IFBLK)
		goto failed;

	st = md_load_super(fd, path);
	if(st == NULL || 
		st->data_offset >= PDM_SECT + (PDM_BLK_SZ / 512))
		pdm = pdm_load_super(fd, path);
	if (st == NULL && pdm == NULL)
		goto failed;

	dev = xmalloc(sizeof(*dev));
	dev->st = st;
	dev->pdm = pdm;
	strncpy(dev->name, path, sizeof(dev->name));
	dev->name[sizeof(dev->name) - 1] = '\0';

failed:

	close(fd);
	return dev;
}

static void free_dev(struct md_dev *dev)
{
	if(dev->st){
		md_free_super(dev->st);
		__list_del(dev->dev_list.prev, dev->dev_list.next);
	}
	if(dev->pdm){
		pdm_free_super(dev->pdm);
		__list_del(dev->pdm_dev_list.prev, dev->pdm_dev_list.next);
	}
	xfree(dev);
}

static void free_md_dev(struct md_ident *id)
{
	struct list *pos, *next;

	list_for_each_safe(pos, next, &id->dev_list) {
		struct md_dev *dev;

		dev = list_entry(pos, struct md_dev, dev_list);
		DPR("free dev %s, %p.\n", dev->name, dev);

		free_dev(dev);
	}

	list_for_each_safe(pos, next, &id->pdm_dev_list) {
		struct md_dev *dev;

		dev = list_entry(pos, struct md_dev, pdm_dev_list);
		DPR("free dev %s, %p.\n", dev->name, dev);

		free_dev(dev);
	}

	xfree(id);
}

static int test_num_and_set(unsigned int num)
{
	static char used_bitmap[MAX_RAID_DEVS + 1];
	char name[16];
	struct stat sts;
	int is_used = 1;

	if (num > MAX_RAID_DEVS)
		return 1;

	if (used_bitmap[num])
		return 1;

	/**
	 * FIXME: We only check if the path is exist.
	 */
	sprintf(name, "/dev/md%u", num);
	if (stat(name, &sts) < 0 && errno == ENOENT)
		is_used = 0;

	used_bitmap[num] = 1;

	DPR("Test for %s, is_used: %u.\n", name, is_used);

	return is_used;
}

static void md_set_num(struct md_ident *id)
{
	char *err_ptr;
	int ret;
	char *nm;
	struct md_info *info = &id->info;

	nm = strchr(info->md_name, ':');
	if (nm)
		nm++;
	else if (info->md_name[0])
		nm = info->md_name;
	else {
		ret = MD_NUM_UNKNOWN;
		goto out;
	}

	ret = strtol(nm, &err_ptr, 10);
	if (*err_ptr != '\0' || ret < 0 || ret >= MAX_RAID_DEVS)
		ret = MD_NUM_UNKNOWN;
	else if (test_num_and_set(ret))
		ret = MD_NUM_UNKNOWN;

out:
	id->md_num = ret;
}

static struct md_ident *new_md_dev(struct md_dev *dev)
{
	struct md_ident *id;

	id = xmalloc(sizeof(*id));
	memset(id, 0, sizeof(*id));
	init_list(&id->dev_list);
	init_list(&id->pdm_dev_list);

	if(dev->st){
		md_get_info(dev->st, &id->info);
		/**
		 * Store the first device's superblock
		 */
		id->st = dev->st;
	}else if(dev->pdm){
		pdm_get_info(dev->pdm, &id->info);
	}else{
		fprintf(stderr, "BUG OCCURED\n");
	}
	
	md_set_num(id);

	DPR("new md %p, st: %p, num: %d\n", id, id->st, id->md_num);

	return id;
}

static void store_md_dev(struct list *dl, struct md_ident *id)
{
	struct list *pos;

	if(id->md_num >= MD_NUM_UNKNOWN) {
		list_add_tail(&id->list, dl);
		return;
	}

	list_for_each(pos, dl) {
		struct md_ident *n;

		n = list_entry(pos, struct md_ident, list);

		if (n->md_num > id->md_num)
			break;
	}

	list_add_tail(&id->list, pos);
}

/**
 * Search which ident has the same superblock, and add to it.
 */
static int store_dev(struct list *md_list, const char *dev_name)
{
	struct list *pos;
	struct md_ident *id;
	struct md_dev *dev;
	int found = 0;


	dev = load_dev(dev_name);
	if (dev == NULL)
		return -1;
	DPR("new dev: %s\n", dev_name);

	list_for_each(pos, md_list) {
		id = list_entry(pos, struct md_ident, list);

		if (id->st && dev->st &&
			md_compare_super(id->st, dev->st) == 0) {
			list_add_tail(&dev->dev_list, &id->dev_list);
			found =1;
		}
		
		if(NULL == id->st && dev->st && 
			md_compare_info(&id->info, dev->st) == 0) {
			md_get_info(dev->st, &id->info);
			id->st = dev->st;
			list_add_tail(&dev->dev_list, &id->dev_list);
			found =1;
		}

		if(dev->pdm && 
			pdm_compare_super(&id->info, dev->pdm) == 0) {
			list_add_tail(&dev->pdm_dev_list, &id->pdm_dev_list);
			found =1;
		}
		
		if(found)
			return 0;
	}

	/**
	 * devices not found. We set a new type.
	 */
	id = new_md_dev(dev);
	if(dev->st)
		list_add(&dev->dev_list, &id->dev_list);
	if(dev->pdm)
		list_add(&dev->pdm_dev_list, &id->pdm_dev_list);
	store_md_dev(md_list, id);

	return 0;
}

static void __load_md_devs(struct list *dlist, const char *patterns[])
{
	glob_t glob_buf;
	int flags = 0;
	const char **pattern = &patterns[0];
	int i;

	free_md_devs(dlist);
	while (*pattern != NULL) {
		glob(*pattern, flags, NULL, &glob_buf);
		flags |= GLOB_APPEND;
		pattern++;
	}
	for (i = 0; i < glob_buf.gl_pathc; i++) {
		char *dev_name = glob_buf.gl_pathv[i];

		DPR("Store device %s:\n", dev_name);

		if (store_dev(dlist, dev_name)) {
			fprintf(stderr, "%s isn't a validate md device.\n",
			        dev_name);
		}
	}

	globfree(&glob_buf);
}

static int find_unused_num(unsigned int start, unsigned int *num)
{
	for (; start <= MAX_RAID_DEVS; start++) {
		if (!test_num_and_set(start)) {
			*num = start;
			return 0;
		}
	}

	return -1;
}

static void arrange_md_num(struct list *dlist)
{
	struct list *pos;
	unsigned int cur_num = 1; /* raid number start from 1, we don't use md0 */

	list_for_each(pos, dlist) {
		struct md_ident *id;

		id = list_entry(pos, struct md_ident, list);
		if (id->md_num == MD_NUM_UNKNOWN) {
			unsigned int num;
			int ret;

			ret = find_unused_num(cur_num, &num);
			if (ret < 0) {
				DPR("Can't find md num for %p\n", id);
				return;
			}
			cur_num = num + 1;
			id->md_num = num;
			DPR("Set %p num to %u\n", id, num);
		}
	}
}

struct list *load_md_devs(struct list *dlist)
{
	__load_md_devs(dlist, dev_patterns);

	arrange_md_num(dlist);

	return dlist;
}

void free_md_devs(struct list *dlist)
{
	struct list *pos, *next;

	list_for_each_safe(pos, next, dlist) {
		struct md_ident *id;

		id = list_entry(pos, struct md_ident, list);
		DPR("free md %p\n", id);

		free_md_dev(id);
	}
}
