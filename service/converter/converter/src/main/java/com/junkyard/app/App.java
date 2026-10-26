package com.junkyard.app;

import org.datavec.image.loader.NativeImageLoader;
import org.nd4j.linalg.api.ndarray.INDArray;
import tools.jackson.databind.*;

import java.io.File;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashMap;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Semaphore;

public class App {
    public static String dataPath = System.getenv("FILE_DIR");
    public static ConcurrentHashMap<User, UserData> userData = new ConcurrentHashMap<User, UserData>();
    public static HashMap<Character, INDArray> charList = new HashMap<Character, INDArray>();

    static void setup() throws IOException, BrokenBitmapException {
        System.out.println("Starting with dataPath " + dataPath);
        Path dirPath = Paths.get(dataPath);
        try {
            Files.createDirectories(dirPath);
        } catch (IOException e) {
            System.out.println(dirPath + " already exists!");
        }
        for (char c : Bitmap.validChars){
            String fullPath = Bitmap.bitmapPath + "char_" + c + ".bmp";
            NativeImageLoader loader = new NativeImageLoader();
            INDArray charMap;
            try {
                charMap = loader.asMatrix(new File(fullPath));
            } catch (IOException e) {
                throw new BrokenBitmapException("Char file does not exist");
            }
            INDArray charMapPreprocessed = Bitmap.transformSingleChar(Bitmap.transform(charMap));
            charList.put(c, charMapPreprocessed);
        }

        Thread t = new Thread(App::cleanupCache, "cleanup");
        t.setDaemon(true);
        t.start();
    }

    public static void main(String[] args) {
        try {
            setup();
        } catch (Exception e) {
            System.err.println("Error setting up data directory!");
            return;
        }

        Semaphore terminated = new Semaphore(0);
        for (String signame : new String[] { "TERM", "INT" }) {
            sun.misc.Signal.handle(new sun.misc.Signal(signame), signal -> {
                terminated.release();
            });
        }

        NetworkInterface n = new NetworkInterface();
        try {
            n.run();
            terminated.acquire();
        } catch (Exception e) {
            System.err.println("Error running socket server");
        } finally {
            n.close();
        }
    }

    private static void cleanupCache() {
        try {
            Thread.sleep(60 * 1000);

            long deadline = Instant.now().getEpochSecond() - 45 * 60;
            userData.entrySet().removeIf(entry -> entry.getValue().cache.getLastUpdate() < deadline);
        } catch (InterruptedException ignored) {
        }
    }
}
