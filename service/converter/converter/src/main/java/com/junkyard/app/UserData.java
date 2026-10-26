package com.junkyard.app;

public class UserData {
    final Cache cache;
    final String path;

    public UserData(Cache cache, String path){
        this.cache = cache;
        this.path = path;
    }

    public void updateCache(CacheEntry entry){
        this.cache.insert(entry);
    }
}
