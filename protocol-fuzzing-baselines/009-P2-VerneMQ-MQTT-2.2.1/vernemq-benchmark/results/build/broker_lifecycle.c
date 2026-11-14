#include <unistd.h>

/* AFLNet's forkserver target lifecycle; the MQTT broker runs separately. */
int main(void)
{
  for (;;) pause();
}
