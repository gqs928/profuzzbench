#define _DEFAULT_SOURCE
#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <signal.h>
#include <stdint.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
static volatile sig_atomic_t stop_requested;
static void on_term(int sig) { (void)sig; stop_requested=1; }
static int read_full(int fd, void *buffer, size_t size) {
  size_t got=0; while(got<size){ssize_t n=read(fd,(char*)buffer+got,size-got);if(n<=0)return 0;got+=(size_t)n;} return 1;
}
static int pg_ready(void) {
  int fd=socket(AF_INET,SOCK_STREAM,0); if(fd<0)return 0;
  struct timeval tv={.tv_sec=1,.tv_usec=0}; (void)setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));
  struct sockaddr_in a={0}; a.sin_family=AF_INET; a.sin_port=htons(26257);
  if(inet_pton(AF_INET,"127.0.0.1",&a.sin_addr)!=1||connect(fd,(struct sockaddr*)&a,sizeof(a))!=0){close(fd);return 0;}
  const char params[]="user\0root\0database\0defaultdb\0client_encoding\0UTF8\0\0";
  const uint32_t len=htonl((uint32_t)(8+sizeof(params)-1)), ver=htonl(196608);
  if(write(fd,&len,4)!=4||write(fd,&ver,4)!=4||write(fd,params,sizeof(params)-1)!=(ssize_t)(sizeof(params)-1)){close(fd);return 0;}
  unsigned char h[5]; int ready=0;
  for(int i=0;i<64;i++){
    if(!read_full(fd,h,5))break;
    uint32_t n; memcpy(&n,h+1,4); n=ntohl(n); if(n<4||n>1048576)break;
    size_t need=n-4,got=0; unsigned char payload[1048576];
    while(got<need){ssize_t r=read(fd,payload+got,need-got);if(r<=0)break;got+=(size_t)r;}
    if(got!=need)break;
    if(h[0]=='R'&&need>=4){uint32_t auth;memcpy(&auth,payload,4);if(ntohl(auth)!=0)break;}
    if(h[0]=='Z'){ready=1;break;}
  }
  close(fd);return ready;
}
static void fail_sample(void){signal(SIGSEGV,SIG_DFL);raise(SIGSEGV);_exit(128+SIGSEGV);}
int main(int argc,char **argv){
  if(argc==2&&strcmp(argv[1],"--once")==0)return pg_ready()?0:1;
  struct sigaction sa={0};sa.sa_handler=on_term;sigemptyset(&sa.sa_mask);if(sigaction(SIGTERM,&sa,NULL)!=0)return 2;
  int up=0;for(int i=0;i<20&&!up;i++){up=pg_ready();if(!up)usleep(100000);}if(!up)return 1;
  while(!stop_requested)pause();
  for(int i=0;i<20;i++){if(pg_ready())return 0;usleep(100000);}fail_sample();return 1;
}
