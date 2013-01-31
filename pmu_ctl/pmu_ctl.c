#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "i2c-dev.h"
#include "pmu_ctl.h"

#define I2C_DEV "/dev/i2c-0"

#define VOUT_EXP	(-9)

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

static int pmu_is_initialized;
static int pmu_fd;

#if 0
static int __pmu_read_byte(uint8_t reg, uint8_t *v)
{
	int ret;

	ret = i2c_smbus_read_byte_data(pmu_fd, reg);
	if (ret == -1)
		return PMU_ERR_IOERR;
	*v = ret;
	return 0;
}
#endif

static int __pmu_read_word(uint8_t reg, uint16_t *v)
{
	int ret;

	ret = i2c_smbus_read_word_data(pmu_fd, reg);
	if (ret == -1)
		return PMU_ERR_IOERR;
	*v = ret;
	return 0;
}

int pmu_init(void)
{
	int fd;

	if (pmu_is_initialized)
		return 0;
	fd = open(I2C_DEV, O_RDWR);
	if (fd < 0)
		return PMU_ERR_NODEV;
	if (ioctl(fd, I2C_SLAVE_FORCE, PMU_ADDRESS) < 0) {
		close(fd);
		return PMU_ERR_NODEV;
	}

	pmu_is_initialized = 1;
	pmu_fd = fd;

	return 0;
}

void pmu_release(void)
{
	if (pmu_is_initialized) {
		close(pmu_fd);
		pmu_is_initialized = 0;
	}
}

#define PMU_CHECK_INIT()	do {		\
	int ret = pmu_init();			\
	if (ret < 0)				\
		return ret;			\
} while (0)

#define CHECK_FAULT(sts, bit, set)	\
	if ((sts) & (bit))				\
		(set) = 1;				\
	else						\
		(set) = 0

static int pmu_get_status(struct pmu_info *info)
{
	uint16_t sts;
	int ret;

	ret = __pmu_read_word(REG_STATUS, &sts);
	if (ret < 0)
		return ret;
	CHECK_FAULT(sts, STS_TEMP_FAULT, info->is_temp_fault);
	CHECK_FAULT(sts, STS_VOUT_FAULT, info->is_vout_fault);
	CHECK_FAULT(sts, STS_VIN_FAULT, info->is_vin_fault);
	CHECK_FAULT(sts, STS_FAN_FAULT, info->is_fan_fault);
	return 0;
}

static int pmu_get_vout(struct pmu_info *info)
{
	uint16_t v;
	int ret;

	ret = __pmu_read_word(REG_VOUT, &v);
	if (ret < 0)
		return ret;
	info->vout = (float)v * pow(2, VOUT_EXP);
	return 0;
}

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

static inline int pmu_read_linear(uint8_t reg, float *out)
{
	uint16_t v;
	int ret;

	ret = __pmu_read_word(reg, &v);
	if (ret < 0)
		return ret;
	*out = pmu_linear_to_real(v);

	return 0;
}

static int pmu_get_vin(struct pmu_info *info)
{
	return pmu_read_linear(REG_VIN, &info->vin);
}

static int pmu_get_temp(struct pmu_info *info)
{
	return pmu_read_linear(REG_TEMP, &info->temp);
}

static int pmu_get_fan_speed(struct pmu_info *info)
{
	return pmu_read_linear(REG_FAN, &info->fan_speed);
}

int pmu_get_info(struct pmu_info *info)
{
	int ret;

	memset(info, 0, sizeof(*info));
	PMU_CHECK_INIT();
	ret = pmu_get_status(info);
	if (ret < 0)
		return ret;
	ret = pmu_get_vout(info);
	if (ret < 0)
		return ret;
	ret = pmu_get_vin(info);
	if (ret < 0)
		return ret;
	ret = pmu_get_temp(info);
	if (ret < 0)
		return ret;
	ret = pmu_get_fan_speed(info);
	if (ret < 0)
		return ret;
	return 0;
}
