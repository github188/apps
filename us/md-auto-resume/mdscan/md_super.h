#ifndef K_MD_SUPER_H
#define K_MD_SUPER_H

#include "list.h"
#include "ktypes.h"

#define MAX_DEV_NAME (32)
#define MAX_RAID_DEVS (32)
#define MD_NUM_UNKNOWN (0xFF)

#define MD_SB_MAGIC		0xa92b4efc

#define MD_FEATURE_BITMAP_OFFSET	1

#define	LEVEL_MULTIPATH		(-4)
#define	LEVEL_LINEAR		(-1)
#define	LEVEL_FAULTY		(-5)


struct super_type;
struct md_info;

struct super_ops {
	int (*load_super)(struct super_type *st, int fd, const char *name);
	void (*free_super)(struct super_type *st);
	int (*compare_super)(struct super_type *st, struct super_type *tst);
	int (*compare_super_info)(struct md_info *info, struct super_type *tst);
	void (*get_info)(struct super_type *st, struct md_info *info);
};

struct super_type {
	int			major;
	int	 		minor;
	int			max_devs;
	u64			data_offset;
	u8			device_uuid[16];
	struct super_ops 	*s_op;
	void 			*superblock; /* data read from disk */
};

struct bitmap_super {
	le32	magic;
	le32	version;
	u8	uuid[16];
	le64	events;
	le64	events_cleared;
	le64	sync_size;
	le32	state;
	le32	chunksize;
	le32	daemon_sleep;
	le32	write_behind;
	u8	pad[256 - 64];
};

struct md_info {
	u8			uuid[16];
	char			md_name[MAX_DEV_NAME];
	unsigned int		major;
	unsigned int		minor;
	int			level;
	unsigned int		raid_disks;
};

struct md_ident {
	char			*dev_name;
	struct md_info		info;
	struct super_type	*st;
	unsigned int		md_num;	/* md1, md2, et al, 0xFF is umset */
	struct list		list;
	struct list		dev_list;
	struct list		pdm_dev_list;
};

static inline int
md_compare_info(struct md_info *info, struct super_type *tst)
{
	return tst->s_op->compare_super_info(info, tst);
}

static inline int
md_compare_super(struct super_type *st, struct super_type *tst)
{
	if (st->major != tst->major ||
	    st->minor != tst->minor)
		return -1;

	return st->s_op->compare_super(st, tst);
}

static inline void md_get_info(struct super_type *st, struct md_info *info)
{
	return st->s_op->get_info(st, info);
}

struct super_type * md_load_super(int fd, const char *name);
void md_free_super(struct super_type *st);

#endif
