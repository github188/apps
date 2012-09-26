#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>

#include "util.h"
#include "md_dev.h"
#include "pdm_info.h"


pdm_super_t * pdm_load_super(int fd, const char *name)
{
	pdm_super_t *st;
	u64 off;

	st = xmalloc(PDM_BLK_SZ);
	memset(st, 0, PDM_BLK_SZ);

	if ((off = lseek64(fd, PDM_SECT * 512, 0)) < 0LL) {
		fprintf(stderr, "Cannot seek to superblock on %s: %s\n",
		        name, strerror(errno));
		goto out_free;
	}

	if (read(fd, st, PDM_BLK_SZ) != PDM_BLK_SZ) {
		fprintf(stderr, "Cannot read superblock on %s\n",
		        name);
		goto out_free;
	}

	st->magic = le64_to_cpu(st->magic);
	if(st->magic != PDM_DEST && 
		st->magic != PDM_SRC){
		fprintf(stderr, "No Pdm info found on %s. Got %llx, expected %llx or %llx\n",
		        name, (unsigned long long)st->magic, PDM_DEST, PDM_SRC);
		goto out_free;
	}else if(st->magic == PDM_DEST){
		DPR("PDM_DEST\n");
	}else if(st->magic == PDM_SRC){
		DPR("PDM_SRC\n");
	}
	
	st->version		= le32_to_cpu(st->version);
	st->level		= le32_to_cpu(st->level);
	st->raid_disks	= le32_to_cpu(st->raid_disks);
	st->buf_size	= le32_to_cpu(st->buf_size);
	st->sleep_ms	= le32_to_cpu(st->sleep_ms);
	st->update_sec	= le32_to_cpu(st->update_sec);
	st->src_size	= le64_to_cpu(st->src_size);
	st->dst_size	= le64_to_cpu(st->dst_size);
	st->end_pos		= le64_to_cpu(st->end_pos);
	return st;

out_free:
	xfree(st);
	return NULL;
}

void pdm_free_super(pdm_super_t *st)
{
	if(st)
		xfree(st);
}

int pdm_compare_super(struct md_info *md_info, pdm_super_t *st)
{
	if (memcmp(md_info->uuid, st->md_uuid,16) != 0)
		return -1;
	if(strncmp(md_info->md_name, (char*)st->md_name, sizeof(st->md_name)-1) != 0)
		return -1;
	if(md_info->level != st->level)
		return -1;
	if(md_info->raid_disks != st->raid_disks)
		return -1;
	return 0;
}

void pdm_get_info(pdm_super_t *st, struct md_info *info)
{
	info->major = 1;
	info->minor = 2;
	info->level = st->level;
	memcpy(info->uuid, st->md_uuid, sizeof(info->uuid));
	strncpy(info->md_name, (char*)st->md_name, sizeof(info->md_name));
	info->raid_disks = st->raid_disks;
}

void pdm_info_clean(struct md_ident *id)
{
	struct list *pos;
	
	//fprintf(fp, "name:%s magic:%smd:/dev/md%u md_uuid=%s ", dev->name, id->md_num, uuid_to_str(pdm->md_uuid));
	list_for_each(pos, &id->pdm_dev_list) {
		int fd, wl;
		pdm_super_t *st;
		struct md_dev *dev;

		dev = list_entry(pos, struct md_dev, pdm_dev_list);
		st = dev->pdm;
		if (NULL == st)
			continue;
		fd = open(dev->name, O_WRONLY | O_EXCL);
		if (fd < 0)
			continue;
		if (lseek64(fd, PDM_SECT * 512, 0) > 0 ) {
			st->magic=0;
			wl = write(fd, st, PDM_BLK_SZ);
		}
		close(fd);
	}
	
}


