#include <stdio.h>
#include <string.h>
#include <errno.h>
#include "dev_manage.h"
#include "util.h"
#include "pdm_info.h"

#define MDSCAN_FILE "/tmp/mdscan"
#define MDSCAN_TMP_FILE "/tmp/.mdscan"

#define PDMSCAN_FILE "/tmp/pdmscan"
#define PDMDEV_FILE "/tmp/pdmdev"

typedef struct mapping {
	char *name;
	int num;
} mapping_t;

mapping_t pers[] = {
	{ "linear", LEVEL_LINEAR},
	{ "raid0", 0},
	{ "0", 0},
	{ "stripe", 0},
	{ "raid1", 1},
	{ "1", 1},
	{ "mirror", 1},
	{ "raid4", 4},
	{ "4", 4},
	{ "raid5", 5},
	{ "5", 5},
	{ "multipath", LEVEL_MULTIPATH},
	{ "mp", LEVEL_MULTIPATH},
	{ "raid6", 6},
	{ "6", 6},
	{ "raid10", 10},
	{ "10", 10},
	{ "raid30", 30},
	{ "30", 30},
	{ "raid50", 50},
	{ "50", 50},
	{ "raid60", 60},
	{ "60", 60},
	{ "raid0+1", 101},
	{ "0+1", 101},
	{ "faulty", LEVEL_FAULTY},
	{ NULL, 0}
};

char *map_num(mapping_t *map, int num)
{
	while (map->name) {
		if (map->num == num)
			return map->name;
		map++;
	}
	return "-unknown-";
}

static void dump_md_dev(struct md_ident *id, FILE *fp)
{
	struct md_info *info = &id->info;
	char *c = map_num(pers, info->level);
	int i;

	fprintf(fp, "ARRAY /dev/md%u level=%s ", id->md_num, c);
	fprintf(fp, "metadata=1.2 ");
	fprintf(fp, "num-devices=%u UUID=", info->raid_disks);
	for (i = 0; i < sizeof(info->uuid); i++) {
		if ((i &3) == 0 && i != 0)
			fprintf(fp, ":");
		fprintf(fp, "%02x", info->uuid[i]);
	}
	if (info->md_name[0])
		fprintf(fp, " name=%.32s", info->md_name);
	fprintf(fp, "\n");
}

pdm_info_stat_t check_md_pdm(struct md_ident *id)
{
	struct md_dev *dev = NULL;
	struct md_dev *dev_dst = NULL;
	struct md_dev *dev_src = NULL;
	struct list *pos = NULL;

	//are pdm devices exist
	if(list_empty(&id->pdm_dev_list))
		goto out_null;

	//found out the source and dest disk of pdm
	list_for_each(pos, &id->pdm_dev_list) {
		dev = list_entry(pos, struct md_dev, pdm_dev_list);
		if(!dev->pdm){
			fprintf(stderr, "BUG, NO PDM INFO!\n");
			goto out_error;
		}
		if(PDM_SRC == dev->pdm->magic
			&& NULL == dev_src){
			dev_src = dev;
		}else if(PDM_DEST == dev->pdm->magic
			&& NULL == dev_dst){
			dev_dst = dev;
		}else{
			fprintf(stderr, "magic %llu, dev %p, src %p, dst %p\n", 
				(unsigned long long)dev->pdm->magic, dev, dev_src, dev_dst);
			dev_dst = NULL;
			dev_src = NULL;
			goto out_error;
		}
	}
	if(NULL == dev_dst || NULL == dev_src){
		fprintf(stderr, "src %p, dst %p\n", dev_src, dev_dst);
		goto out_error;
	}
	
	//check the pdm parameters
	//src
	if(!dev_src->st)
		goto out_error;
	if(memcmp(dev_src->pdm->src_uuid, id->st->device_uuid, 16) != 0)
		goto out_error;
	if(memcmp(dev_src->pdm->md_uuid, id->info.uuid, 16) != 0)
		goto out_error;
	if(dev_src->pdm->end_pos == 0)
		goto out_error;
	if(dev_src->pdm->end_pos > dev_src->pdm->src_size)
		goto out_error;
	if(dev_src->pdm->end_pos > dev_src->pdm->dst_size)
		goto out_error;

	//dest
	if(memcmp(dev_dst->pdm->md_uuid, id->info.uuid, 16) != 0)
		goto out_error;
	if(dev_dst->pdm->end_pos == 0)
		goto out_error;
	if(dev_dst->pdm->end_pos > dev_dst->pdm->src_size)
		goto out_error;
	if(dev_dst->pdm->end_pos > dev_dst->pdm->dst_size)
		goto out_error;
	//if(dev_dst->st)
	//	goto out_error;

	//src vs dest
	if(memcmp(dev_src->pdm->pdm_uuid, dev_dst->pdm->pdm_uuid, 16) != 0)
		goto out_error;
	if(memcmp(dev_src->pdm->src_uuid, dev_dst->pdm->src_uuid, 16) != 0)
		goto out_error;
	if(memcmp(dev_src->pdm->dst_uuid, dev_dst->pdm->dst_uuid, 16) != 0)
		goto out_error;
	if(dev_src->pdm->src_size != dev_dst->pdm->src_size)
		goto out_error;
	if(dev_src->pdm->dst_size != dev_dst->pdm->dst_size)
		goto out_error;
	
	return pdm_ok;
out_error:
	fprintf(stderr, "PDM INFO ERRER\n");
	return pdm_bad;
out_null:
	return pdm_null;
	
}

void dump_md_pdm(struct md_ident *id, FILE *fp)
{
	struct list *pos;
	struct md_info *info = &id->info;
	struct md_dev *dev;
	pdm_super_t *pdm = NULL;
	unsigned long long off = 0;;

	fprintf(fp, "md=/dev/md%u md_uuid=%s ", id->md_num, uuid_to_str(info->uuid));
	
	list_for_each(pos, &id->pdm_dev_list) {

		dev = list_entry(pos, struct md_dev, pdm_dev_list);
		pdm = dev->pdm;
		if(pdm->magic == PDM_DEST){
			fprintf(fp, "dst=%s ", dev->name);
		}else if(pdm->magic == PDM_SRC){
			fprintf(fp, "src=%s ", dev->name);
		}
		if(0 == off || off > pdm->end_pos)
			off = pdm->end_pos;
	}
	fprintf(fp, "off=%llu ", off);
	fprintf(fp, "buf_size=%u ", (unsigned int)pdm->buf_size);
	fprintf(fp, "sleep_ms=%u ", (unsigned int)pdm->sleep_ms);
	fprintf(fp, "update_sec=%u ", (unsigned int)pdm->update_sec);
	fprintf(fp, "\n");
}

void dump_pdm_dev(struct md_ident *id, FILE *fp)
{
	struct list *pos;
	
	//fprintf(fp, "name:%s magic:%smd:/dev/md%u md_uuid=%s ", dev->name, id->md_num, uuid_to_str(pdm->md_uuid));
	list_for_each(pos, &id->pdm_dev_list) {
		struct md_dev *dev;
		pdm_super_t *pdm;
		dev = list_entry(pos, struct md_dev, pdm_dev_list);
		pdm = dev->pdm;
		fprintf(fp, "dev_name:%s ", dev->name);
		fprintf(fp, "magic:%s ", magic_to_str(pdm->magic));
		fprintf(fp, "md_name:/dev/md%u ", id->md_num);
		fprintf(fp, "md_uuid:%s ", uuid_to_str(pdm->md_uuid));
		fprintf(fp, "pdm_uuid:%s ", uuid_to_str(pdm->pdm_uuid));
		fprintf(fp, "src_uuid:%s ", uuid_to_str(pdm->src_uuid));
		fprintf(fp, "dst_uuid:%s ", uuid_to_str(pdm->dst_uuid));
		fprintf(fp, "src_size:%llu ", (unsigned long long)pdm->src_size);
		fprintf(fp, "dst_size:%llu ", (unsigned long long)pdm->dst_size);
		fprintf(fp, "end_pos:%llu ", (unsigned long long)pdm->end_pos);
		fprintf(fp, "\n");
	}
}


static void dump_md_pattern(const char **pattern, FILE *fp)
{
	while (*pattern != NULL) {
		fprintf(fp, "DEVICE %s\n", *pattern);
		pattern++;
	}
}

static void dump_md_devs(struct list *dl)
{
	struct list *pos;
	FILE *fp, *pdm_fp, *dev_fp;
	int is_has_dev = 0;
	pdm_info_stat_t pdm_stat = pdm_ok;

	fp = fopen(MDSCAN_TMP_FILE, "w");
	pdm_fp = fopen(PDMSCAN_FILE, "w");
	dev_fp = fopen(PDMDEV_FILE, "w");
	if (fp == NULL) {
		fprintf(stderr, "Can't open file %s: %s\n", MDSCAN_TMP_FILE,
		        strerror(errno));
		return;
	}

	dump_md_pattern(dev_patterns, fp);

	list_for_each(pos, dl) {
		struct md_ident *id;

		id = list_entry(pos, struct md_ident, list);
		if (id->md_num == MD_NUM_UNKNOWN) {
			/**
			 * TOTO: print some information here.
			 */
			DPR("md_num unset for %p.\n", id);
			continue;
		}
		if(id->st){
			dump_md_dev(id, fp);
			is_has_dev = 1;
		}

		pdm_stat = check_md_pdm(id);
		if(pdm_ok == pdm_stat && pdm_fp)
			dump_md_pdm(id, pdm_fp);
		if(pdm_null != pdm_stat)
			dump_pdm_dev(id, dev_fp);
		if(pdm_bad == pdm_stat)
			pdm_info_clean(id);
	}
	fclose(dev_fp);
	fclose(pdm_fp);
	fclose(fp);

	if (is_has_dev)
		rename(MDSCAN_TMP_FILE, MDSCAN_FILE);
}

int main(int argc, char *argv[])
{
	LIST(dlist);

	load_md_devs(&dlist);
	dump_md_devs(&dlist);
	free_md_devs(&dlist);

	return 0;
}
