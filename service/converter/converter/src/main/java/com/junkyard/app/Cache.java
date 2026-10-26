package com.junkyard.app;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;

public class Cache {
    private final ArrayList<CacheEntry> cache = new ArrayList<>();
    private long lastUpdate = 0;

    public synchronized void insert(CacheEntry entry){
        this.cache.add(entry);
        this.lastUpdate = Instant.now().getEpochSecond();
    }

    public synchronized void remove(CacheEntry entry) {
        this.cache.remove(entry);
    }

    public synchronized CacheEntry getByName(String fileName){
        for (CacheEntry entry : this.cache){
            if (entry.fileName.equals(fileName)) {
                return entry;
            }
        }
        return null;
    }

    public synchronized CacheEntry getByOcr(String ocr){
        for (CacheEntry entry : this.cache){
            if (entry.ocrData.equals(ocr)) {
                return entry;
            }
        }
        return null;
    }

    public synchronized CacheEntry getReference(){
        return this.cache.get(0);
    }

    public synchronized long getLastUpdate(){
        return this.lastUpdate;
    }
}
