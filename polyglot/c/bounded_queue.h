#ifndef POLYGLOT_BOUNDED_QUEUE_H
#define POLYGLOT_BOUNDED_QUEUE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct bb_queue bb_queue_t;

typedef enum {
    BB_OK = 0,
    BB_TIMEOUT = 1,
    BB_CLOSED = 2,
    BB_INVALID = 3,
    BB_NOMEM = 4,
    BB_ERROR = 5
} bb_status_t;

bb_queue_t *bb_queue_create(size_t capacity);
void bb_queue_close(bb_queue_t *queue);
void bb_queue_destroy(bb_queue_t *queue);
bb_status_t bb_queue_push(bb_queue_t *queue, uint64_t value, uint32_t timeout_ms);
bb_status_t bb_queue_pop(bb_queue_t *queue, uint64_t *value, uint32_t timeout_ms);
size_t bb_queue_size(const bb_queue_t *queue);
size_t bb_queue_capacity(const bb_queue_t *queue);

#ifdef __cplusplus
}
#endif

#endif
