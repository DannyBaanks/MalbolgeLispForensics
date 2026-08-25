
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/time.h>
#include <errno.h>
#include <signal.h>
#include <unistd.h>

#define u8   uint8_t
#define i32  int32_t
#define u32 uint32_t
#define i64  int64_t
#define u64 uint64_t
#define C      const
#define P     static
#define _(a...) {return({a;});}
#define F_(n,a...) for(int i=0;i<n;i++){a;}
#define F1(n,x,a...) for(i32 i=0;i<n;i+=x){a;}

#define INLINE P inline __attribute__((always_inline))
#define assert(X) if(!(X))__builtin_unreachable();
#define LKL(c) __builtin_expect((c),1)

typedef u32 W;
#define SZ 19
#define END 1162261467ULL

P C u8 crz[]={1,0,0,9,1,0,2,9,2,2,1},crz2[]={4,3,3,1,0,0,1,0,0,9,9,9,9,9,9,9,4,3,5,1,0,2,1,0,2,9,9,9,9,9,9,9,5,5,4,2,2,1,2,2,1,9,9,9,9,9,9,9,4,3,3,1,0,0,7,6,6,9,9,9,9,9,9,9,4,3,5,1,0,2,7,6,8,9,9,9,9,9,9,9,5,5,4,2,2,1,8,8,7,9,9,9,9,9,9,9,7,6,6,7,6,6,4,3,3,9,9,9,9,9,9,9,7,6,8,7,6,8,4,3,5,9,9,9,9,9,9,9,8,8,7,8,8,7,5,5,4,9,9,9,9,9,9,9};
#define UNR_CRZ(trans,sf1,sf2)W am=a%sf1,ad=a/sf1,dm=d%sf1,dd=d/sf1;r+=k*trans[am+sf2*dm];a=ad;d=dd;k*=sf1;
INLINE W mcrz(W a, W d){W r=0,k=1;
#pragma GCC unroll 16
F_(SZ/2,UNR_CRZ(crz2,9,16))if(SZ&1){UNR_CRZ(crz,3,4)}return r;}
INLINE W mrot(W x)_(W t=END/3,b=x%t,m=b%3,d=b/3;d+m*(t/3)+(x-b))

P u64 pgsiz;
P W*mem,pat[6];

static struct timeval dbg_t0;
volatile unsigned long long dbg_faults=0;
unsigned long long dbg_steps_global=0;
static double dbg_elap(void){struct timeval n;gettimeofday(&n,NULL);return (n.tv_sec-dbg_t0.tv_sec)+(n.tv_usec-dbg_t0.tv_usec)/1e6;}
#define DBGP(...) do{fprintf(stderr,"DBG [%.1fs] ",dbg_elap());fprintf(stderr,__VA_ARGS__);fflush(stderr);}while(0)

static void dbg_heartbeat(int _){
  extern unsigned long long dbg_steps_global;
  char b[160];int n=snprintf(b,sizeof b,"HB [%.1fs] steps=%llu faults=%llu\n",dbg_elap(),dbg_steps_global,dbg_faults);
  if(n>0)write(2,b,(size_t)n);
  struct itimerval it={{5,0},{5,0}};setitimer(ITIMER_REAL,&it,NULL);
}

P void mpstb(void*b,u64 l){int r=mprotect(b,l,PROT_READ|PROT_WRITE);if(r){fprintf(stderr,"DBG mprotect FAIL r=%d errno=%d\n",r,errno);fflush(stderr);}}

P void sigsegvh(int n,siginfo_t*si,void*_) {
  extern volatile unsigned long long dbg_faults;
  dbg_faults++;
  void*a=si->si_addr,*ab=(void*)((u64)a&~(pgsiz-1));mpstb(ab, pgsiz);
  W* curr=ab;i64 off=(curr-mem)%(END/3);F1(pgsiz,sizeof(W),*curr++=pat[off++%6]);}

P u64 rup(u64 v)_(((v-1)&~(pgsiz-1))+pgsiz)

#define RDS 65536
__attribute__((hot,flatten))int main(int argc, char* argv[]){
  gettimeofday(&dbg_t0,NULL);DBGP("start argc=%d argv1=%s\n",argc,argc>1?argv[1]:"(none)");
  pgsiz=sysconf(_SC_PAGESIZE);mem=mmap(NULL,END*sizeof(W),PROT_NONE,MAP_NORESERVE|MAP_PRIVATE|MAP_ANON,-1,0);
  DBGP("reserve done mem=%p\n",(void*)mem);
  struct sigaction act;memset(&act,0,sizeof(struct sigaction));act.sa_flags=SA_SIGINFO;act.sa_sigaction=sigsegvh;sigaction(SIGSEGV,&act,NULL);
  DBGP("heartbeat DISABLED\n");
  FILE*f=fopen(argv[1],"rb");DBGP("fopen=%p argv1=%s errno=%d\n",(void*)f,argc>1?argv[1]:"(none)",f?0:errno);fflush(stderr);if(!f){fprintf(stderr,"DBG ABORT_NULL_FILE\n");return 3;}fseek(f,0,SEEK_END);u64 S=ftell(f);rewind(f);DBGP("filesize=%llu\n",(unsigned long long)S);fflush(stderr);u64 szR=rup(S),off=0;DBGP("pre-mpstb szR=%llu\n",(unsigned long long)szR);fflush(stderr);mpstb(mem, szR*sizeof(W));DBGP("post-mpstb\n");char data[RDS];
  C W a1_off=94-((END-1)/6-29524)%94,a2_off=94-((END-1)/3-59048)%94;{unsigned long long dbg_iter=0;while(S){int am=LKL(S>RDS)?RDS:S;if(dbg_iter<3){DBGP("iter#%llu am=%d\n",dbg_iter,am);fflush(stderr);}dbg_iter++;if((dbg_iter%100000000ULL)==0){fprintf(stderr,"DBG iter=%llu\n",dbg_iter);fflush(stderr);}fread(&data,1,am,f);
  #pragma GCC unroll 32
  F_(am,W w=data[i];mem[off++]=w)S-=am;}DBGP("load-done off=%llu iters=%llu\n",(unsigned long long)off,dbg_iter);for(;off<szR;off++)mem[off]=mcrz(mem[off-1],mem[off-2]);DBGP("fill-done\n");}
  W n2=mem[off-2],n1=mem[off-1];u64 off2=off;F_(6,W n0=mcrz(n1,n2);pat[off2%6]=n0;n2=n1;n1=n0;off2++)W c=0,a=0,*d=mem;
  DBGP("pattern-done, dispatching\n");
  P C int offs[]={0,((i64)a1_off-(i64)(END/3))%94+94,((i64)a2_off-(i64)(2*(END/3))%94+94)};P C void*j[94];F_(94,j[i]=&&INS_DEF)
  #define M(n) j[n]=&&INS_##n;
  M(4)M(5)M(23)M(39)M(40)M(62)M(68)M(81)
  #define BRA {goto*j[(c+mem[c]+offs[c/(END/3)])%94];}
  BRA;
  unsigned long long dbg_steps=0;struct timeval dbg_n;
  #define NXT do{mem[c] = \
    "SOMEBODY MAKE ME FEEL ALIVE" \
    "[hj9>,5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@" \
    "AND SHATTER ME"[mem[c]];c++;d++;dbg_steps++;dbg_steps_global++; \
    if((dbg_steps_global&536870911ULL)==0){char b[160];int n=snprintf(b,sizeof b,"DBG steps=%llu c=%u d=%ld a=%u faults=%llu elapsed=%.1fs\n",dbg_steps_global,c,(i64)(d-mem),a,dbg_faults,dbg_elap());if(n>0){ssize_t wn=write(2,b,(size_t)n);(void)wn;}} \
    BRA;}while(0)
  INS_4:c=*d;NXT;INS_5:{static int dbg_pn=0;if(!dbg_pn++)DBGP("first putchar ENTERING\n");putchar(a);if(dbg_pn<4)DBGP("putchar #%d done a=%u\n",dbg_pn,a);}fflush(stdout);NXT;
  INS_23:;{static int dbg_gn=0;if(!dbg_gn++)DBGP("first getchar ENTERING\n");int CR=getchar();if(dbg_gn<4){DBGP("getchar #%d -> %d\n",dbg_gn,CR);}a=CR==EOF?END-1:CR;}NXT;INS_39:a=*d=mrot(*d);NXT;INS_40:d=mem+*d;NXT;
  INS_62:a=*d=mcrz(a, *d);INS_68:NXT;INS_81:fprintf(stderr,"DBG HALT steps=%llu c=%u d=%ld a=%u\n",dbg_steps,c,(i64)(d-mem),a);return 0;INS_DEF:NXT;
}




