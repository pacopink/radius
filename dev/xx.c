#include <stdlib.h>
#include <stdio.h>

int main()
{
#if defined(__GNUC__)
    printf("__GNUC__\n");
#else
    printf("XXXXXXXX\n");
#endif
    return 0;
}
