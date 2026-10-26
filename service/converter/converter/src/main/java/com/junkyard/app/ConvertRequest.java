package com.junkyard.app;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.Base64;

public class ConvertRequest {
    public User owner;
    public String path;
    public String action;
    public String data;

    public byte[] execute(){
        UserData userData;
        byte[] rawData;
        try {
            rawData = Base64.getDecoder().decode(data);
            userData = App.userData.get(this.owner);
        } catch (IllegalArgumentException e){
            return "Invalid action: broken encoding".getBytes();
        } catch (Exception e) {
            return "Unknown decoding error".getBytes();
        }
        final Path userPath = Paths.get(userData.path);
        switch (this.action) {
            case "ITT" -> {
                Path outPath = userPath;
                String filePathStr = outPath + "/" + this.path.toUpperCase();
                Path filePath = Paths.get(filePathStr);
                try {
                    Files.write(filePath, rawData, StandardOpenOption.CREATE_NEW);
                } catch (IOException e){
                    e.printStackTrace();
                    return "ITT: Could not write user input to file".getBytes();
                }
                Bitmap b;
                try {
                    b = new Bitmap(filePath);
                } catch (BrokenBitmapException e){
                    return ("ITT: " + e.getMessage()).getBytes();
                }
                String res;
                try{
                    res = b.ocr();
                } catch (IOException e) {
                    return ("ITT: " + e.getMessage()).getBytes();
                }
                CacheEntry entry = new CacheEntry(filePathStr, res);
                userData.updateCache(entry);
                return res.getBytes(StandardCharsets.UTF_8);
            }
            case "TTI" -> {
                Bitmap b;
                try{
                    b = new Bitmap(rawData);
                } catch (BrokenBitmapException e){
                    return "TTI: Bitmap generation failed".getBytes();
                }
                Path outPath = userPath;
                String filePathStr = outPath + "/" + this.path.toUpperCase();
                Path filePath = Paths.get(filePathStr);
                try {
                    b.save(filePath);
                } catch (IOException e) {
                    e.printStackTrace();
                    return ("TTI: Could not save file: " + e.getMessage()).getBytes();
                }
                byte[] fileData;
                try{
                    fileData = Files.readAllBytes(filePath);
                } catch (IOException e) {
                    e.printStackTrace();
                    return ("TTI: Could not read back file: " + e.getMessage()).getBytes();
                }
                CacheEntry entry = new CacheEntry(filePathStr, new String(rawData, StandardCharsets.UTF_8));
                userData.updateCache(entry);
                return fileData;
            }
            case "GET" -> {
                Path outPath = userPath;
                if (this.path.length() > 255){
                    return "Filename too long!".getBytes();
                }
                String filePathStr = outPath + "/" + this.path.toUpperCase();
                Path filePath = Paths.get(filePathStr);
                byte[] fileData = null;
                try {
                    fileData = Files.readAllBytes(filePath);
                } catch (IOException e) {
                    String error = e.getMessage().split(": ")[1];
                    if (error.startsWith("File name too long")){
                        return ("This file name is too long, this is how a filename should look like: " + userData.cache.getReference().fileName).getBytes();
                    }
                    return "File does not exist".getBytes();
                }
                return fileData;
            }
        }
        return "Invalid action: Converter action unknown".getBytes();
    }
}


