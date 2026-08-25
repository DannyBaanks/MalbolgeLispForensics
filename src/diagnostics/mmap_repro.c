#include <stdio.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdint.h>

#define END 1162261467ULL

int main(void) {
    long ps = sysconf(_SC_PAGESIZE);
    printf("pagesize=%ld\n", ps); fflush(stdout);

    uint32_t *mem = mmap(NULL, END * sizeof(uint32_t), PROT_NONE,
                         MAP_NORESERVE | MAP_PRIVATE | MAP_ANON, -1, 0);
    printf("reserve=%p\n", (void *)mem); fflush(stdout);
    if (mem == MAP_FAILED) { perror("mmap-reserve"); return 1; }

    void *r = mmap(mem, 65536 * sizeof(uint32_t), PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANON | MAP_FIXED, -1, 0);
    printf("flip-fixed r=%p\n", r); fflush(stdout);
    if (r == MAP_FAILED) { perror("mmap-fixed"); return 2; }

    for (size_t i = 0; i < 65536; i++) mem[i] = (uint32_t)i;
    printf("write-through ok mem[65535]=%u\n", mem[65535]); fflush(stdout);

    printf("DONE\n");
    return 0;
}
