package com.example.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SmsPartResultsCheck {
    @Test
    fun singlePartNeedsItsCallback() {
        val parts = SmsPartResults(1)
        assertNull(parts.status)
        assertTrue(parts.recordPart(0, true))
        assertEquals("sent", parts.status)
        assertEquals(1, parts.sentParts)
    }

    @Test
    fun multipartSucceedsOnlyAfterEveryCallbackInAnyOrder() {
        val parts = SmsPartResults(3)
        assertTrue(parts.recordPart(2, true))
        assertTrue(parts.recordPart(0, true))
        assertNull(parts.status)
        assertTrue(parts.recordPart(1, true))
        assertEquals("sent", parts.status)
        assertEquals(3, parts.sentParts)
        assertEquals(3, parts.totalParts)
    }

    @Test
    fun oneFailedPartMakesTheCompletedSendFail() {
        val parts = SmsPartResults(3)
        assertTrue(parts.recordPart(2, true))
        assertTrue(parts.recordPart(0, false))
        assertNull(parts.status)
        assertTrue(parts.recordPart(1, true))
        assertEquals("failed", parts.status)
        assertEquals(2, parts.sentParts)
    }

    @Test
    fun missingCallbacksNeverReportSuccessOrFailure() {
        val parts = SmsPartResults(3)
        assertNull(parts.status)
        assertTrue(parts.recordPart(0, false))
        assertTrue(parts.recordPart(1, true))
        assertNull(parts.status)
        assertEquals(1, parts.sentParts)
    }

    @Test
    fun duplicateCallbacksCannotChangeARecordedResult() {
        val parts = SmsPartResults(2)
        assertTrue(parts.recordPart(0, false))
        assertFalse(parts.recordPart(0, true))
        assertNull(parts.status)
        assertTrue(parts.recordPart(1, true))
        assertFalse(parts.recordPart(1, false))
        assertEquals("failed", parts.status)
        assertEquals(1, parts.sentParts)
    }

    @Test
    fun invalidIndexesDoNotCompleteAnyPart() {
        val parts = SmsPartResults(1)
        assertFalse(parts.recordPart(-1, true))
        assertFalse(parts.recordPart(1, false))
        assertNull(parts.status)
        assertEquals(0, parts.sentParts)
        assertTrue(parts.recordPart(0, true))
        assertEquals("sent", parts.status)
    }
}
