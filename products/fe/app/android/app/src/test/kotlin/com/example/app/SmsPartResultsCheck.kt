package com.example.app

fun main() {
    val single = SmsPartResults(1)
    check(single.status == null)
    check(single.recordPart(0, true))
    check(single.status == "sent" && single.sentParts == 1)
    check(!single.recordPart(0, false))
    check(single.status == "sent")

    val partial = SmsPartResults(3)
    check(!partial.recordPart(-1, true))
    check(!partial.recordPart(3, true))
    check(partial.recordPart(2, true))
    check(partial.recordPart(0, false))
    check(partial.status == null)
    check(partial.recordPart(1, true))
    check(partial.status == "failed" && partial.sentParts == 2)

    val complete = SmsPartResults(2)
    check(complete.recordPart(1, true))
    check(complete.status == null)
    check(complete.recordPart(0, true))
    check(complete.status == "sent" && complete.totalParts == 2)
    println("SMS part aggregation checks passed")
}
