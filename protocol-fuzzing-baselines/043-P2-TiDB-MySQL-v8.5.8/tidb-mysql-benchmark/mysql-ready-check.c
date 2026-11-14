#define _DEFAULT_SOURCE
#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <signal.h>
#include <stdint.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
#ifndef MYSQL_PORT
#define MYSQL_PORT 3306
#endif
static volatile sig_atomic_t stop_requested;
static void on_term(int sig){(void)sig;stop_requested=1;}
static int read_full(int fd,void *p,size_t n){size_t g=0;while(g<n){ssize_t r=read(fd,(char*)p+g,n-g);if(r<=0)return 0;g+=(size_t)r;}return 1;}
static int ready(void){
  int fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return 0;
  struct timeval tv={.tv_sec=1,.tv_usec=0};(void)setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv));
  struct sockaddr_in a={0};a.sin_family=AF_INET;a.sin_port=htons(MYSQL_PORT);
  if(inet_pton(AF_INET,"127.0.0.1",&a.sin_addr)!=1||connect(fd,(struct sockaddr*)&a,sizeof(a))!=0){close(fd);return 0;}
  unsigned char h[4];if(!read_full(fd,h,4)){close(fd);return 0;}
  uint32_t n=(uint32_t)h[0]|((uint32_t)h[1]<<8)|((uint32_t)h[2]<<16);
  unsigned char payload[256];if(n==0||n>sizeof(payload)||!read_full(fd,payload,n)){close(fd);return 0;}
  close(fd);return payload[0]==0x0a;
}
static void fail_sample(void){signal(SIGSEGV,SIG_DFL);raise(SIGSEGV);_exit(128+SIGSEGV);}
int main(int argc,char **argv){
  if(argc==2&&strcmp(argv[1],"--once")==0)return ready()?0:1;
  struct sigaction sa={0};sa.sa_handler=on_term;sigemptyset(&sa.sa_mask);if(sigaction(SIGTERM,&sa,NULL)!=0)return 2;
  int up=0;for(int i=0;i<20&&!up;i++){up=ready();if(!up)usleep(100000);}if(!up)return 1;
  while(!stop_requested)pause();
  for(int i=0;i<20;i++){if(ready())return 0;usleep(100000);}fail_sample();return 1;
}
