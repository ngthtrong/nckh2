package com.example.app

import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit.SECONDS
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PteShutdownCheck {
    @Test(timeout = 15_000)
    fun waitsForRunningInferenceAndQueuedWorkBeforeClosing() {
        val executor = Executors.newSingleThreadExecutor()
        val started = CountDownLatch(1)
        val finish = CountDownLatch(1)
        val events = ConcurrentLinkedQueue<String>()
        val inference = executor.submit {
            started.countDown()
            finish.await()
            events.add("forward")
        }
        val queued = executor.submit { events.add("queued") }
        try {
            assertTrue(started.await(5, SECONDS))
            shutdownPte(executor) {
                check(inference.isDone) { "Cannot destroy module while method is executing" }
                events.add("close")
            }
            assertTrue(executor.isShutdown)
            assertTrue(events.isEmpty())
            assertFalse(inference.isCancelled)
            finish.countDown()
            inference.get(5, SECONDS)
            queued.get(5, SECONDS)
            assertTrue(executor.awaitTermination(5, SECONDS))
            assertEquals(listOf("forward", "queued", "close"), events.toList())
        } finally {
            finish.countDown()
            executor.shutdownNow()
        }
    }

    @Test(timeout = 15_000)
    fun closesModuleLoadedWhileShutdownWasRequested() {
        val executor = Executors.newSingleThreadExecutor()
        val started = CountDownLatch(1)
        val finish = CountDownLatch(1)
        val module = AtomicReference<AutoCloseable?>()
        val closes = AtomicInteger()
        val load = executor.submit {
            started.countDown()
            finish.await()
            module.set(AutoCloseable { closes.incrementAndGet() })
        }
        try {
            assertTrue(started.await(5, SECONDS))
            shutdownPte(executor) { module.get()?.close() }
            assertEquals(0, closes.get())
            finish.countDown()
            load.get(5, SECONDS)
            assertTrue(executor.awaitTermination(5, SECONDS))
            assertEquals(1, closes.get())
        } finally {
            finish.countDown()
            executor.shutdownNow()
        }
    }
}
