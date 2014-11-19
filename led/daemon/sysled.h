#ifndef SYSLED__H__
#define SYSLED__H__

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

bool sb_gpio28_set(bool sw);
bool sb_gpio28_set_atom(bool sw);

#ifdef __cplusplus
}
#endif

#endif // SYSLED__H__
