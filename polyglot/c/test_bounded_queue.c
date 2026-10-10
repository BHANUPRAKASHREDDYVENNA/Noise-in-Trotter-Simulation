#include "bounded_queue.h"

#include <assert.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>

static void test_basic(void) {
    bb_queue_t *queue = bb_queue_create(2U);
    assert(queue != NULL);
    assert(bb_queue_capacity(queue) == 2U);
    assert(bb_queue_size(queue) == 0U);

    assert(bb_queue_push(queue, 11U, 0U) == BB_OK);
    assert(bb_queue_push(queue, 22U, 0U) == BB_OK);
    assert(bb_queue_push(queue, 33U, 1U) == BB_TIMEOUT);

    uint64_t value = 0U;
    assert(bb_queue_pop(queue, &value, 0U) == BB_OK);
    assert(value == 11U);
    assert(bb_queue_pop(queue, &value, 0U) == BB_OK);
    assert(value == 22U);

    bb_queue_close(queue);
    assert(bb_queue_push(queue, 44U, 0U) == BB_CLOSED);
    assert(bb_queue_pop(queue, &value, 0U) == BB_CLOSED);
    assert(bb_queue_pop(NULL, &value, 0U) == BB_INVALID);
    assert(bb_queue_pop(queue, NULL, 0U) == BB_INVALID);
    bb_queue_destroy(queue);
}

typedef struct {
    bb_queue_t *queue;
} thread_args_t;

static void *producer(void *arg) {
    thread_args_t *args = arg;
    for (uint64_t i = 1U; i <= 1000U; ++i) {
        while (bb_queue_push(args->queue, i, 1000U) == BB_TIMEOUT) {
        }
    }
    bb_queue_close(args->queue);
    return NULL;
}

static void *consumer(void *arg) {
    thread_args_t *args = arg;
    uint64_t expected = 1U;
    uint64_t value = 0U;
    for (;;) {
        bb_status_t status = bb_queue_pop(args->queue, &value, 1000U);
        if (status == BB_CLOSED) {
            break;
        }
        assert(status == BB_OK);
        assert(value == expected);
        expected++;
    }
    assert(expected == 1001U);
    return NULL;
}

static void test_concurrency(void) {
    bb_queue_t *queue = bb_queue_create(8U);
    assert(queue != NULL);
    thread_args_t args = {queue};
    pthread_t producer_thread;
    pthread_t consumer_thread;
    assert(pthread_create(&producer_thread, NULL, producer, &args) == 0);
    assert(pthread_create(&consumer_thread, NULL, consumer, &args) == 0);
    assert(pthread_join(producer_thread, NULL) == 0);
    assert(pthread_join(consumer_thread, NULL) == 0);
    bb_queue_destroy(queue);
}

int main(void) {
    test_basic();
    test_concurrency();
    puts("C bounded queue tests passed.");
    return 0;
}
