#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "freeradius-devel/build.h"
#include "freeradius-devel/libradius.h"
#include "eap_sim.h"

int main()
{
    uint8_t mk[20];
    uint8_t fk[160];
    struct eapsim_keys key;
    memset(&key, 0, sizeof(key));

    eapsim_calculate_keys(&key);
    eapsim_dump_mk(&key);
    fips186_2prf(mk, fk);

    printf("OK\n");
}
