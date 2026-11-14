/* 通过 JVMTI 方法边覆盖，将 Kafka Java 服务端路径写进 AFL 共享图。 */
#define _GNU_SOURCE
#include <jni.h>
#include <jvmti.h>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/shm.h>

#define KAFKA_AFL_MAP_SIZE 65536U
#define METHOD_TABLE_SIZE 131072U

typedef struct {
  jmethodID method;
  uint32_t location;
} method_entry_t;

static unsigned char *coverage_map;
static method_entry_t method_table[METHOD_TABLE_SIZE];
static pthread_mutex_t method_table_lock = PTHREAD_MUTEX_INITIALIZER;

static uint32_t hash_bytes(uint32_t hash, const char *text)
{
  if (!text) return hash;
  while (*text) {
    hash ^= (unsigned char)*text++;
    hash *= 16777619U;
  }
  return hash;
}

/* AFL 只反馈 KafkaApis 的请求入口，避免后台线程和调度顺序污染稳定度。 */
static int kafka_apis_class(const char *signature)
{
  return signature && strstr(signature, "Lkafka/server/KafkaApis;") != NULL;
}

static int kafka_protocol_method(const char *name)
{
  return name &&
      (!strcmp(name, "handle") ||
       !strcmp(name, "handleApiVersionsRequest") ||
       !strcmp(name, "handleTopicMetadataRequest") ||
       !strcmp(name, "handleProduceRequest") ||
       !strcmp(name, "handleFetchRequest"));
}

static size_t method_slot(jmethodID method)
{
  uintptr_t key = ((uintptr_t)method >> 3) * 2654435761U;
  return (size_t)(key & (METHOD_TABLE_SIZE - 1U));
}

static void remember_method(jmethodID method, uint32_t location)
{
  size_t slot = method_slot(method);
  pthread_mutex_lock(&method_table_lock);
  for (size_t probe = 0; probe < METHOD_TABLE_SIZE; probe++) {
    method_entry_t *entry = &method_table[(slot + probe) &
                                          (METHOD_TABLE_SIZE - 1U)];
    if (entry->method == method) {
      entry->location = location;
      break;
    }
    if (!entry->method) {
      entry->location = location;
      __atomic_store_n(&entry->method, method, __ATOMIC_RELEASE);
      break;
    }
  }
  pthread_mutex_unlock(&method_table_lock);
}

static uint32_t lookup_method(jmethodID method)
{
  size_t slot = method_slot(method);
  for (size_t probe = 0; probe < METHOD_TABLE_SIZE; probe++) {
    method_entry_t *entry = &method_table[(slot + probe) &
                                          (METHOD_TABLE_SIZE - 1U)];
    jmethodID known = __atomic_load_n(&entry->method, __ATOMIC_ACQUIRE);
    if (known == method) return entry->location;
    if (!known) return UINT32_MAX;
  }
  return UINT32_MAX;
}

static void JNICALL on_class_prepare(jvmtiEnv *jvmti, JNIEnv *jni,
                                     jthread thread, jclass klass)
{
  char *class_signature = NULL;
  jmethodID *methods = NULL;
  jint method_count = 0;
  (void)jni;
  (void)thread;

  if ((*jvmti)->GetClassSignature(jvmti, klass, &class_signature, NULL) !=
          JVMTI_ERROR_NONE || !kafka_apis_class(class_signature))
    goto cleanup;
  if ((*jvmti)->GetClassMethods(jvmti, klass, &method_count, &methods) !=
      JVMTI_ERROR_NONE)
    goto cleanup;

  for (jint index = 0; index < method_count; index++) {
    char *method_name = NULL;
    char *method_signature = NULL;
    uint32_t hash = 2166136261U;
    if ((*jvmti)->GetMethodName(jvmti, methods[index], &method_name,
                                &method_signature, NULL) == JVMTI_ERROR_NONE &&
        kafka_protocol_method(method_name)) {
      hash = hash_bytes(hash, class_signature);
      hash = hash_bytes(hash, "#");
      hash = hash_bytes(hash, method_name);
      hash = hash_bytes(hash, method_signature);
      remember_method(methods[index], hash & (KAFKA_AFL_MAP_SIZE - 1U));
    }
    if (method_name)
      (*jvmti)->Deallocate(jvmti, (unsigned char *)method_name);
    if (method_signature)
      (*jvmti)->Deallocate(jvmti, (unsigned char *)method_signature);
  }

cleanup:
  if (methods) (*jvmti)->Deallocate(jvmti, (unsigned char *)methods);
  if (class_signature)
    (*jvmti)->Deallocate(jvmti, (unsigned char *)class_signature);
}

static void JNICALL on_method_entry(jvmtiEnv *jvmti, JNIEnv *jni,
                                    jthread thread, jmethodID method)
{
  uint32_t location;
  (void)jvmti;
  (void)jni;
  (void)thread;

  if (!coverage_map) return;
  location = lookup_method(method);
  if (location == UINT32_MAX) return;
  /* 记录方法是否执行，不累计调用次数，隔离 JVM 后台线程的调度波动。 */
  __atomic_store_n(&coverage_map[location], 1U, __ATOMIC_RELAXED);
}

JNIEXPORT jint JNICALL Agent_OnLoad(JavaVM *vm, char *options, void *reserved)
{
  jvmtiEnv *jvmti = NULL;
  jvmtiCapabilities capabilities;
  jvmtiEventCallbacks callbacks;
  const char *shm_id = getenv("__AFL_SHM_ID");
  (void)options;
  (void)reserved;

  if (shm_id && *shm_id) {
    char *end = NULL;
    long id = strtol(shm_id, &end, 10);
    if (end && *end == '\0' && id >= 0)
      coverage_map = (unsigned char *)shmat((int)id, NULL, 0);
    if (coverage_map == (void *)-1) coverage_map = NULL;
  }
  if ((*vm)->GetEnv(vm, (void **)&jvmti, JVMTI_VERSION_1_2) != JNI_OK || !jvmti)
    return JNI_ERR;

  memset(&capabilities, 0, sizeof(capabilities));
  capabilities.can_generate_method_entry_events = 1;
  if ((*jvmti)->AddCapabilities(jvmti, &capabilities) != JVMTI_ERROR_NONE)
    return JNI_ERR;
  memset(&callbacks, 0, sizeof(callbacks));
  callbacks.ClassPrepare = on_class_prepare;
  callbacks.MethodEntry = on_method_entry;
  if ((*jvmti)->SetEventCallbacks(jvmti, &callbacks, sizeof(callbacks)) !=
      JVMTI_ERROR_NONE)
    return JNI_ERR;
  if ((*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
                                          JVMTI_EVENT_CLASS_PREPARE, NULL) !=
          JVMTI_ERROR_NONE ||
      (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
                                          JVMTI_EVENT_METHOD_ENTRY, NULL) !=
          JVMTI_ERROR_NONE)
    return JNI_ERR;
  return JNI_OK;
}

JNIEXPORT void JNICALL Agent_OnUnload(JavaVM *vm)
{
  (void)vm;
  if (coverage_map) {
    shmdt(coverage_map);
    coverage_map = NULL;
  }
}
