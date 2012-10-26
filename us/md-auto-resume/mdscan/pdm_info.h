#ifndef __PDM_INFO_H__
#define __PDM_INFO_H__

#define PDM_BLK_SZ (1024)
#define PAGE_SIZE (4096)
#define PDM_SECT (((1 << 20) - PAGE_SIZE) / 512)

#define PDM_DEST 0x50444D5F44455354LL
#define PDM_SRC 0x50444D5F53524300LL

/**  PDM �����������Ϣ*/
typedef struct pdm_super_s {
	/****************

	****************/
	///PDM��Ϣ���
	//Ŀ����Ϊ�ַ���PDM_DEST
	//Դ��Ϊ�ַ���PDM_SRC
	le64 magic;
	///��Ϣ�汾�̶�Ϊ0
	le32 version;
	///Դ��UUID
	u8 src_uuid[16];
	///Ŀ����UUID
	u8 dst_uuid[16];
	///Դ�̴�С
	le64 src_size;
	///Ŀ���̴�С
	le64 dst_size;
	///��ɵ�λ��
	le64 end_pos;
	/****************

	****************/
	///PDM ��������󻺴�
	le32 buf_size;
	///����ʱ��
	le32 sleep_ms;
	///��Ϣ����ʱ��
	le32 update_sec;
	/****************

	****************/
	///������UUID
	u8 pdm_uuid[16];
	///RAID��UUID
	u8 md_uuid[16];
	///RAID������
	u8 md_name[32];
	///RAID����
	le32 level;
	///RAID������
	le32 raid_disks;
	///����
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

