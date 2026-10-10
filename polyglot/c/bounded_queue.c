#define _POSIX_C_SOURCE 200809L

#include "bounded_queue.h"

#include <errno.h>
#include <pthread.h>
#include <stdlib.h>
#include <time.h>

#define BB_WAIT_FOREVER UINT32_MAX

typedef struct {
    pthread_mutex_t mutex;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
    uint64_t *items;
    size_t capacity;
    size_t head;
    size_t tail;
    size_t size;
    int closed;
} bb_queue_impl_t;

struct bb_queue {
    bb_queue_impl_t impl;
};

static int timespec_after_ms(struct timespec *deadline, uint32_t timeout_ms) {
    struct timespec now;
    if (deadline == NULL) {
        return EINVAL;
    }
    if (clock_gettime(CLOCK_REALTIME, &now) != 0) {
        return errno == 0 ? EIO : errno;
    }
    deadline->tv_sec = now.tv_sec + (time_t)(timeout_ms / 1000U);
    long extra_ns = (long)(timeout_ms % 1000U) * 1000000L;
    deadline->tv_nsec = now.tv_nsec + extra_ns;
    if (deadline->tv_nsec >= 1000000000L) {
        deadline->tv_sec += 1;
        deadline->tv_nsec -= 1000000000L;
    }
    return 0;
}

static bb_status_t lock_queue(bb_queue_t *queue) {
    if (queue == NULL) {
        return BB_INVALID;
    }
    return pthread_mutex_lock(&queue->impl.mutex) == 0 ? BB_OK : BB_ERROR;
}

bb_queue_t *bb_queue_create(size_t capacity) {
    if (capacity == 0U) {
        return NULL;
    }

    bb_queue_t *queue = calloc(1U, sizeof(*queue));
    if (queue == NULL) {
        return NULL;
    }

    queue->impl.items = calloc(capacity, sizeof(*queue->impl.items));
    if (queue->impl.items == NULL) {
        free(queue);
        return NULL;
    }
    queue->impl.capacity = capacity;

    if (pthread_mutex_init(&queue->impl.mutex, NULL) != 0) {
        free(queue->impl.items);
        free(queue);
        return NULL;
    }
    if (pthread_cond_init(&queue->impl.not_empty, NULL) != 0) {
        pthread_mutex_destroy(&queue->impl.mutex);
        free(queue->impl.items);
        free(queue);
        return NULL;
    }
    if (pthread_cond_init(&queue->impl.not_full, NULL) != 0) {
        pthread_cond_destroy(&queue->impl.not_empty);
        pthread_mutex_destroy(&queue->impl.mutex);
        free(queue->impl.items);
        free(queue);
        return NULL;
    }
    return queue;
}

void bb_queue_close(bb_queue_t *queue) {
    if (lock_queue(queue) != BB_OK) {
        return;
    }
    queue->impl.closed = 1;
    (void)pthread_cond_broadcast(&queue->impl.not_empty);
    (void)pthread_cond_broadcast(&queue->impl.not_full);
    (void)pthread_mutex_unlock(&queue->impl.mutex);
}

void bb_queue_destroy(bb_queue_t *queue) {
    if (queue == NULL) {
        return;
    }
    (void)pthread_cond_destroy(&queue->impl.not_empty);
    (void)pthread_cond_destroy(&queue->impl.not_full);
    (void)pthread_mutex_destroy(&queue->impl.mutex);
    free(queue->impl.items);
    free(queue);
}

bb_status_t bb_queue_push(bb_queue_t *queue, uint64_t value, uint32_t timeout_ms) {
    if (queue == NULL) {
        return BB_INVALID;
    }
    bb_status_t status = lock_queue(queue);
    if (status != BB_OK) {
        return status;
    }

    struct timespec deadline;
    if (timeout_ms != BB_WAIT_FOREVER && timespec_after_ms(&deadline, timeout_ms) != 0) {
        (void)pthread_mutex_unlock(&queue->impl.mutex);
        return BB_ERROR;
    }

    while (queue->impl.size == queue->impl.capacity && !queue->impl.closed) {
        int rc = timeout_ms == BB_WAIT_FOREVER
            ? pthread_cond_wait(&queue->impl.not_full, &queue->impl.mutex)
            : pthread_cond_timedwait(&queue->impl.not_full, &queue->impl.mutex, &deadline);
        if (rc == ETIMEDOUT) {
            (void)pthread_mutex_unlock(&queue->impl.mutex);
            return BB_TIMEOUT;
        }
        if (rc != 0) {
            (void)pthread_mutex_unlock(&queue->impl.mutex);
            return BB_ERROR;
        }
    }

    if (queue->impl.closed) {
        (void)pthread_mutex_unlock(&queue->impl.mutex);
        return BB_CLOSED;
    }

    queue->impl.items[queue->impl.tail] = value;
    queue->impl.tail = (queue->impl.tail + 1U) % queue->impl.capacity;
    queue->impl.size++;
    (void)pthread_cond_signal(&queue->impl.not_empty);
    (void)pthread_mutex_unlock(&queue->impl.mutex);
    return BB_OK;
}

bb_status_t bb_queue_pop(bb_queue_t *queue, uint64_t *value, uint32_t timeout_ms) {
    if (queue == NULL || value == NULL) {
        return BB_INVALID;
    }
    bb_status_t status = lock_queue(queue);
    if (status != BB_OK) {
        return status;
    }

    struct timespec deadline;
    if (timeout_ms != BB_WAIT_FOREVER && timespec_after_ms(&deadline, timeout_ms) != 0) {
        (void)pthread_mutex_unlock(&queue->impl.mutex);
        return BB_ERROR;
    }

    while (queue->impl.size == 0U && !queue->impl.closed) {
        int rc = timeout_ms == BB_WAIT_FOREVER
            ? pthread_cond_wait(&queue->impl.not_empty, &queue->impl.mutex)
            : pthread_cond_timedwait(&queue->impl.not_empty, &queue->impl.mutex, &deadline);
        if (rc == ETIMEDOUT) {
            (void)pthread_mutex_unlock(&queue->impl.mutex);
            return BB_TIMEOUT;
        }
        if (rc != 0) {
            (void)pthread_mutex_unlock(&queue->impl.mutex);
            return BB_ERROR;
        }
    }

    if (queue->impl.size == 0U && queue->impl.closed) {
        (void)pthread_mutex_unlock(&queue->impl.mutex);
        return BB_CLOSED;
    }

    *value = queue->impl.items[queue->impl.head];
    queue->impl.head = (queue->impl.head + 1U) % queue->impl.capacity;
    queue->impl.size--;
    (void)pthread_cond_signal(&queue->impl.not_full);
    (void)pthread_mutex_unlock(&queue->impl.mutex);
    return BB_OK;
}

size_t bb_queue_size(const bb_queue_t *queue) {
    if (queue == NULL) {
        return 0U;
    }
    bb_queue_t *mutable_queue = (bb_queue_t *)(void *)queue;
    if (lock_queue(mutable_queue) != BB_OK) {
        return 0U;
    }
    size_t size = mutable_queue->impl.size;
    (void)pthread_mutex_unlock(&mutable_queue->impl.mutex);
    return size;
}

size_t bb_queue_capacity(const bb_queue_t *queue) {
    if (queue == NULL) {
        return 0U;
    }
    return queue->impl.capacity;
}
