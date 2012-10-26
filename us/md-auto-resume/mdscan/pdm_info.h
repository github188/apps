#ifndef __PDM_INFO_H__
#define __PDM_INFO_H__

#define PDM_BLK_SZ (1024)
#define PAGE_SIZE (4096)
#define PDM_SECT (((1 << 20) - PAGE_SIZE) / 512)

#define PDM_DEST 0x50444D5F44455354LL
#define PDM_SRC 0x50444D5F53524300LL

/**  PDM 操作保存的信息*/
typedef struct pdm_super_s {
	/****************

	****************/
	///PDM信息标记
	//目标盘为字符串PDM_DEST
	//源盘为字符串PDM_SRC
	le64 magic;
	///信息版本固定为0
	le32 version;
	///源盘UUID
	u8 src_uuid[16];
	///目标盘UUID
	u8 dst_uuid[16];
	///源盘大小
	le64 src_size;
	///目标盘大小
	le64 dst_size;
	///完成的位置
	le64 end_pos;
	/****************

	****************/
	///PDM 操作的最大缓存
	le32 buf_size;
	///休眠时间
	le32 sleep_ms;
	///信息更新时间
	le32 update_sec;
	/****************

	****************/
	///操作的UUID
	u8 pdm_uuid[16];
	///RAID组UUID
	u8 md_uuid[16];
	///RAID组名称
	u8 md_name[32];
	///RAID级别
	le32 level;
	///RAID组盘数
	le32 raid_disks;
	///保留
	u8 reserved[1]; 
} pdm_super_t;

typedef enum{
	pdm_ok = 0,
	pdm_null,
	pdm_bad,
}pdm_info_stat_t;

pdm_super_t * pdm_load_super(int fd, const char *name);
void pdm_free_super(pdm_super_t *st);
int pdm_compare_super(struct md_info *md_info, pdm_super_t *st);
void pdm_get_info(pdm_super_t *st, struct md_info *info);
void dump_md_pdm(struct md_ident *id, FILE *fp);;
void pdm_info_clean(struct md_ident *id);

#define to_ascii(c) ((c) < 10 ? (c) + '0' : (c) - 10 + 'A')
#define uuid_to_str(md_uuid)\
({\
	static char uustr[40];\
	char c;\
	int i;\
	memset(uustr, 0, sizeof(uustr));\
	for(i=0;i<16;i++){\
		c = md_uuid[i] /0x10 & 0x0f;\
		uustr[i*2] = to_ascii(c);\
		c = md_uuid[i] & 0x0f;\
		uustr[i*2+1] = to_ascii(c);\
	}\
	uustr;\
})
#define magic_to_str(magic)\
({\
	static char str[16];\
	int i;\
	memset(str, 0, sizeof(str));\
	for(i = 0; i < sizeof(magic);i++){\
		str[i] = ((magic) >> ((sizeof(magic) - 1 - i) * 8)) & 0xff;\
	}\
	str;\
})

#endif

