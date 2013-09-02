#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <strings.h>
#include <time.h>
#include <string.h>
#include "pmu-info.h"

#define VOUT_EXP	(-9)

#define CHECK_FAULT(sts, bit, set)	\
	if ((sts) & (bit))				\
		(set) = 1;				\
	else						\
		(set) = 0

enum {
	REG_STATUS	= 0x79,
	REG_VIN		= 0x88,
	REG_VOUT	= 0x8b,
	REG_TEMP	= 0x8e, /* read the hotspot only */
	REG_FAN		= 0x90,

	STS_TEMP_FAULT	= (1 << 2),
	STS_VIN_FAULT	= (1 << 3),
	STS_VOUT_FAULT	= (1 << 5),
	STS_FAN_FAULT	= (1 << 10)
};

static float pmu_linear_to_real(uint16_t v)
{
	/* Linear format for PM Bus:
	 * 15 14 13 12 11    10 9 8 7 6 5 4 3 2 1 0
	 * 2's comp exp        2'comp data
	 */
	int16_t exp, data;

	data = v & 0x7ff;
	data = (data << 5) >> 5; /* do 2's comp */
	exp = v & 0xf800;
	exp = exp >> 11; /* do 2's comp */

	return (float)data * pow(2, (float)exp);
}

int pmu_get_info(const char *dev, struct pmu_info *info1, int check_temp)
{
	FILE *fp;
	char line[128];
	unsigned long sts, vin, vout, fan, temp_amb, temp_hs;

	fp = fopen(dev, "r");
	if (!fp)
	{
		return -1;
	}

	fread(line, sizeof(line), 1, fp);
	fclose(fp);

	//line[24] = '\0';
	sscanf(line, "%lx %lx %lx %lx %lx %lx",
		&sts, &vin, &vout, &fan, &temp_amb, &temp_hs);
	bzero(info1, sizeof(struct pmu_info));
	CHECK_FAULT(sts, STS_TEMP_FAULT, info1->is_temp_fault);
	CHECK_FAULT(sts, STS_VIN_FAULT, info1->is_vin_fault);
	CHECK_FAULT(sts, STS_VOUT_FAULT, info1->is_vout_fault);
	CHECK_FAULT(sts, STS_FAN_FAULT, info1->is_fan_fault);
	info1->vin = pmu_linear_to_real(vin);
	info1->vout = vout * pow(2, VOUT_EXP);
	info1->fan_speed = pmu_linear_to_real(fan);
	info1->temp = pmu_linear_to_real(temp_amb);

	/* 因拔掉电源线后再重新拔插电源模块导致取到的sts状态不对，
	 * 所以补充判断输入电压的数值
	 */
	if (info1->vin < 100.0)
		info1->is_vin_fault = 1;

	/* 设置电源风扇转速后，风扇状态位报警，
	 * 所以补充判断风扇转速
	 */
	if (info1->fan_speed > 4000.0)
		info1->is_fan_fault = 0;

#ifdef _DEBUG
	printf("module%c, sts: 0x%x, vin: %.1f(0x%x), vout: %.1f(0x%x), "
			"fan_speed: %.1f(0x%x), temp_amb: %.1f(0x%x), temp_hs: %.1f(0x%x)\n",
			dev[strlen(dev)-1], sts, info1->vin, vin, info1->vout, vout,
			info1->fan_speed, fan, info1->temp, temp_amb,
			pmu_linear_to_real(temp_hs), temp_hs);
#endif

	/* 根据温度调整风扇转速
	 * 设定三个高中低温度值，超过最高值时全速运转，超过中间值时提高10%，
	 * 降低到最低值以下时降低10%
	 * 由调用者确定是否检测
	 */
#define POWER_TEMP_HI	45
#define POWER_TEMP_MI	38
#define POWER_TEMP_LO	32
#define POWER_CHECK_INTERVAL	60
	char buf[64] = { '\0' };
	if (!check_temp)
		return 0;

	if (info1->temp > POWER_TEMP_HI)
	{
		strcpy(buf, "fan_speed set 100");
	} else if (info1->temp > POWER_TEMP_MI) {
		strcpy(buf, "fan_speed inc 10");
	} else if (info1->temp < POWER_TEMP_LO) {
		strcpy(buf, "fan_speed dec 10");
	} else {
		return 0;
	}

	fp = fopen(dev, "w");
	if (!fp)
	{
		return -1;
	}
	fwrite(buf, strlen(buf), 1, fp);
	fclose(fp);

	return 0;
}
