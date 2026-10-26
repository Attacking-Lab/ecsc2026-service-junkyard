package com.junkyard.app;
import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;

import tools.jackson.databind.ObjectMapper;

public class NetworkInterface {
    HttpServer httpServer;

    public void run() throws IOException {
        try {
            httpServer = HttpServer.create(new InetSocketAddress(9305), 100);
            httpServer.createContext("/process", new ConnectionHandler());
            try {
                httpServer.start();
            } catch (Exception e){
                System.out.println(e.getStackTrace());
            }

            System.out.println("Server is running on port 9305");
        } catch (IOException e) {
            System.out.println("Error starting the server: " + e.getMessage());
        }
    }

    static boolean validatePath (String s){
        Pattern p = Pattern.compile("^\\p{L}+\\.(bmp|txt)$");
        Matcher m = p.matcher(s);
        return m.find();
    }

    public void close(){
        this.httpServer.stop(0);
    }

    static class ConnectionHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException
        {
            String body = new String(
                exchange.getRequestBody().readAllBytes(),
                StandardCharsets.UTF_8
            );
            ConvertRequest r;
            ObjectMapper mapper = new ObjectMapper();
            try {
                r = mapper.readValue(body, ConvertRequest.class);
            } catch (Exception e){
                e.printStackTrace();
                String result = "Request parsing failed";
                exchange.sendResponseHeaders(400, 0);
                OutputStream os = exchange.getResponseBody();
                os.write(result.getBytes(StandardCharsets.UTF_8));
                os.close();
                return;
            }
            boolean valid = validatePath(r.path);
            if (!valid){
                String result = "Illegal path";
                exchange.sendResponseHeaders(400, 0);
                OutputStream os = exchange.getResponseBody();
                os.write(result.getBytes(StandardCharsets.UTF_8));
                os.close();
                return;
            }
            if (!App.userData.containsKey(r.owner)){
                UUID uuid = UUID.randomUUID();
                String fileDir = App.dataPath + "/" + uuid;
                try {
                    Files.createDirectories(Paths.get(fileDir));
                } catch (Exception e){
                    String result = "Failed to create a directory for the user";
                    exchange.sendResponseHeaders(400, 0);
                    OutputStream os = exchange.getResponseBody();
                    os.write(result.getBytes(StandardCharsets.UTF_8));
                    os.close();
                    return;
                }
                String ownerFile = fileDir + "/" + "owner.json";
                mapper.writeValue(new File(ownerFile), r.owner);
                UserData data = new UserData(new Cache(), fileDir);
                App.userData.put(r.owner, data);
            }
            byte[] result;
            try {
                result = r.execute();
            } catch (RuntimeException e) {
                e.printStackTrace();
                exchange.sendResponseHeaders(500, 0);
                OutputStream os = exchange.getResponseBody();
                os.write("cannot convert".getBytes(StandardCharsets.UTF_8));
                os.close();
                return;
            }
            exchange.sendResponseHeaders(200, 0);
            OutputStream os = exchange.getResponseBody();
            os.write(result);
            os.close();
        }
    }
}
