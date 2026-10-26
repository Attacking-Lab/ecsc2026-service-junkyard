package com.junkyard.app;

import java.time.Instant;

public class CacheEntry {
    final String fileName;
    final String ocrData;
    final Instant ts;

    public CacheEntry (String fileName, String ocrData){
        this.ts = Instant.now();
        this.fileName = fileName;
        this.ocrData = ocrData;
    }
}
