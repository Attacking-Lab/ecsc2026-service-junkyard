/* ==========================================================================
 *                                  IMPORTANT
 * ==========================================================================
 * This is a lot of code that does not contain any intended vulnerabilities.
 * All known exploit paths do not require a bug in here.
 */

package com.junkyard.app;

import org.datavec.image.loader.NativeImageLoader;
import org.nd4j.linalg.api.buffer.DataType;
import org.nd4j.linalg.api.ndarray.INDArray;
import org.nd4j.linalg.factory.Nd4j;
import org.nd4j.linalg.indexing.NDArrayIndex;
import org.nd4j.linalg.ops.transforms.Transforms;

import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;

public class Bitmap {
    static int characterWidth = 25;
    static int characterHeight = 50;
    static Character[] validChars = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '_', '{', '}'};
    static HashSet<Character> validCharSet = new HashSet<>(Arrays.asList(validChars));
    static String bitmapPath = "static/font-bitmaps/";
    long fileSize;
    long dataOffset;
    long secondHeaderSize;
    long width;
    long height;
    long size;
    INDArray img;
    byte[] rawImage;

    public Bitmap(Path path) throws BrokenBitmapException {
        byte[] data;
        try{
            data = Files.readAllBytes(path);
        } catch (IOException e) {
            throw new BrokenBitmapException("File does not exist");
        }
        // first 2 bytes are header 0-2
        if (data.length < 2){
            throw new BrokenBitmapException("Broken bitmap");
        }
        if (!((data[0] == (byte) 0x42) && (data[1] == (byte) 0x4d))){
            throw new BrokenBitmapException("Broken bitmap");
        }
        // next 4 bytes are file size 2-6
        if (data.length < 6){
            throw new BrokenBitmapException("Broken bitmap");
        }
        byte[] tmp = Arrays.copyOfRange(data,2,6);
        this.fileSize = ByteBuffer.wrap(tmp).order(ByteOrder.LITTLE_ENDIAN).getInt();
        // 4 bytes uninteresting 6-10
        // 4 bytes data offset 10-14
        if (data.length < 14){
            throw new BrokenBitmapException("Broken bitmap");
        }
        tmp = Arrays.copyOfRange(data,10,14);
        this.dataOffset = ByteBuffer.wrap(tmp).order(ByteOrder.LITTLE_ENDIAN).getInt();
        if (this.dataOffset != 54){
            throw new BrokenBitmapException("Broken bitmap");
        }
        // 4 bytes second header size 14-18
        if (data.length < 18){
            throw new BrokenBitmapException("Broken bitmap");
        }
        tmp = Arrays.copyOfRange(data,14,18);
        this.secondHeaderSize = ByteBuffer.wrap(tmp).order(ByteOrder.LITTLE_ENDIAN).getInt();
        if (this.secondHeaderSize != 40){
            throw new BrokenBitmapException("Broken bitmap");
        }
        // 4 bytes image width 18-22
        if (data.length < 22){
            throw new BrokenBitmapException("Broken bitmap");
        }
        tmp = Arrays.copyOfRange(data,18,22);
        this.width = ByteBuffer.wrap(tmp).order(ByteOrder.LITTLE_ENDIAN).getInt();
        // only multiples of character width
        if ((this.width % characterWidth) != 0){
            throw new BrokenBitmapException("Broken bitmap");
        }
        // at most 50 characters
        if (this.width > (characterWidth * 50L)){
            throw new BrokenBitmapException("Bitmap too big");
        }
        // 4 bytes image height 22-26
        if (data.length < 26){
            throw new BrokenBitmapException("Broken bitmap");
        }
        tmp = Arrays.copyOfRange(data,22,26);
        this.height = ByteBuffer.wrap(tmp).order(ByteOrder.LITTLE_ENDIAN).getInt();
        // only multiples of character width
        if ((this.height % characterHeight) != 0){
            throw new BrokenBitmapException("Broken bitmap");
        }
        // 2 bytes useless 26-28
        // 2 bytes bits per pixel 28-30
        if (data.length < 30){
            throw new BrokenBitmapException("Broken bitmap");
        }
        tmp = Arrays.copyOfRange(data,28, 30);
        int bbp = ByteBuffer.wrap(tmp).order(ByteOrder.LITTLE_ENDIAN).getShort();
        // always 32
        if (bbp != 32){
            throw new BrokenBitmapException("Broken bitmap");
        }
        // 4 bytes compression, always 0 30-34
        if (data.length < 34){
            throw new BrokenBitmapException("Broken bitmap");
        }
        tmp = Arrays.copyOfRange(data,30, 34);
        int compression = ByteBuffer.wrap(tmp).order(ByteOrder.LITTLE_ENDIAN).getInt();
        if (compression != 0){
            throw new BrokenBitmapException("Broken bitmap");
        }
        // 4 bytes image size 34-38
        if (data.length < 38){
            throw new BrokenBitmapException("Broken bitmap");
        }
        tmp = Arrays.copyOfRange(data,34, 38);
        this.size = ByteBuffer.wrap(tmp).order(ByteOrder.LITTLE_ENDIAN).getInt();
        // 16 bytes unused 38-54
        // rest is actual content
        if ((this.size + 54) > Integer.MAX_VALUE) {
            throw new BrokenBitmapException("Broken bitmap");
        }
        if (this.size != (this.width * this.height * 4)){
            throw new BrokenBitmapException("Broken bitmap");
        }
        int total_size = (int) this.size + 54;
        if (data.length < total_size){
            throw new BrokenBitmapException("Broken bitmap");
        }
        rawImage = Arrays.copyOfRange(data,54, total_size);
        NativeImageLoader loader = new NativeImageLoader();
        try {
            this.img = loader.asMatrix(new File(path.toUri()));
        } catch (IOException e) {
            throw new BrokenBitmapException("File does not exist");
        }
    }

    public Bitmap(byte[] data) throws BrokenBitmapException {
        if (data.length > 40) {
            throw new BrokenBitmapException("Too much data");
        }
        StringBuilder buildInput = new StringBuilder();
        for (byte b: data){
            char casted_byte = (char) b;
            if (validCharSet.contains(casted_byte)){
                buildInput.append(casted_byte);
            }
        }
        String input = buildInput.toString();
        // we assume a single line of text
        this.width = (long) input.length() * characterWidth;
        this.height = characterHeight;
        // the final data, built incrementally
        ArrayList<Byte> image = new ArrayList<>();
        // first 2 bytes are header 0-2
        image.add((byte) 0x42);
        image.add ((byte) 0x4d);
        // next 4 bytes are file size 2-6
        size = width * height * 4;
        int tmp_size = (int) (54 + size);
        byte[] length = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(tmp_size).array();
        for (byte b: length)
            image.add(b);
        // 4 bytes uninteresting 6-10
        image.add((byte) 0);
        image.add((byte) 0);
        image.add((byte) 0);
        image.add((byte) 0);
        // 4 bytes data offset 10-14
        byte[] dataOffset = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(54).array();
        for (byte b: dataOffset)
            image.add(b);
        // 4 bytes second header size 14-18
        byte[] secondHeaderSize = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(40).array();
        for (byte b: secondHeaderSize)
            image.add(b);
        // 4 bytes image width 18-22
        byte[] imageWidth = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt((int) width).array();
        for (byte b: imageWidth)
            image.add(b);
        // 4 bytes image height 22-26
        byte[] imageHeight = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt((int) height).array();
        for (byte b: imageHeight)
            image.add(b);
        // 2 bytes useless 26-28, always 1
        byte[] constant = ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN).putShort((short) 1).array();
        for (byte b: constant)
            image.add(b);
        // 2 bytes bits per pixel 28-30
        byte[] bbp = ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN).putShort((short) 32).array();
        for (byte b: bbp)
            image.add(b);
        // 4 bytes compression, always 0 30-34
        byte[] compression = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt((int) 0).array();
        for (byte b: compression)
            image.add(b);
        // 4 bytes image size in bytes 34-38
        byte[] imgSize = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt((int) size).array();
        for (byte b: imgSize)
            image.add(b);
        // 16 bytes unused 38-54
        for (int i = 0; i<16;i++)
            image.add((byte) 0);
        // rest is actual content
        // step 1: populate the loadArray
        byte[][] loadArray = new byte[input.length()][characterWidth * characterHeight * 4];
        for (int i = 0; i<input.length(); i++){
            char c = input.charAt(i);
            String fullPath = bitmapPath + "char_" + c + ".bmp";
            Bitmap charMap = new Bitmap(Paths.get(fullPath));
            loadArray[i] = charMap.rawImage;
        }
        // step 2: create rawImage, line by line. We know the order is
        // first row of all images, second row of all images,...
        // line by line
        for (int line = 0; line<characterHeight;line++){
            // for each character in the string
            for (int i = 0; i<input.length(); i++){
                // the bitmap that we look at
                byte [] currentMap = loadArray[i];
                // index where to start copying: the width of an image in bytes * the current line
                int index = line * characterWidth * 4;
                for (int j = index; j<(index+characterWidth*4); j++){
                    image.add(currentMap[j]);
                }
            }
        }
        byte raw[] = new byte[image.size()];
        for (int i = 0; i<image.size(); i++)
            raw[i] = image.get(i);
        rawImage = raw;
        // step 3: do the conversion as we did it in the other constructor
        // h x w
        byte[][][] img = new byte[(int) this.height][(int) this.width][3];//
        for (int column_index = 0; column_index < (this.height); column_index++){
            for (int row_index = 0; row_index < (this.width); row_index++){
                for (int i = 0; i<3; i++){
                    // data index: column_index * 4 * this.width + row_index * 4
                    int index = (int) (column_index * (this.width * 4) + row_index * 4 + i);
                    int flipped_index = (int) this.height - column_index - 1;
                    // flip 0 and 2, dont save alpha (assume always 0xff)
                    if (i == 0){
                        img[flipped_index][row_index][2] = rawImage[index];
                    } else if (i == 2){
                        img[flipped_index][row_index][0] = rawImage[index];
                    } else {
                        img[flipped_index][row_index][i] = rawImage[index];
                    }
                }
            }
        }
        INDArray hwc = Nd4j.createFromArray(img);
        INDArray chw = hwc.permute(2, 0, 1).dup();
        INDArray nchw = chw.reshape(1, chw.size(0), chw.size(1), chw.size(2));
        this.img = nchw.castTo(DataType.UINT32);;
    }

    static long diffNonnegative(INDArray char1, INDArray char2){
        INDArray diff = char1.sub(char2);                 // element-wise a - b (new array)
        INDArray result = Transforms.abs(diff);
        return result.sumNumber().longValue();
    }

    static INDArray preprocess(INDArray arr){
        INDArray bg = arr.get(NDArrayIndex.all(), NDArrayIndex.all(), NDArrayIndex.interval(0,1), NDArrayIndex.interval(0,1));
        INDArray result = arr.sub(bg);
        Transforms.abs(result, false);
        return result;
    }

    static INDArray transform(INDArray arr){
        INDArray wide = arr.castTo(DataType.INT32);
        INDArray summed = wide.sum(false, 1);
        return summed;
    }

    static INDArray transformSingleChar(INDArray arr){
        INDArray mask = arr.gt(6).castTo(DataType.INT32);          // 1.0 where value > 6, else 0.0
        INDArray result = mask.mul(255);
        return result;
    }

    char matchChar(INDArray arr) throws BrokenBitmapException, IOException {
        long bestValue = 50000;
        char result = 0;
        INDArray arrPreprocessed = transform(preprocess(arr));
        INDArray normalized = transformSingleChar(arrPreprocessed);
        for (char c : validChars){
            INDArray charMapPreprocessed = App.charList.get(c);
            long diff = diffNonnegative(normalized, charMapPreprocessed);
            if (diff < bestValue) {
                bestValue = diff;
                result = c;
            }
        }
        return result;
    }

    INDArray cutChar (int heightIndex, int widthIndex){
        long num_row_chars = this.width / characterWidth;
        long num_column_chars = this.height / characterHeight;
        int widthStart = widthIndex * characterWidth;
        int heightStart = heightIndex * characterHeight;
        if ((heightIndex >= num_column_chars) || (widthIndex >= num_row_chars)){
            throw new IllegalArgumentException();
        }
        return this.img.get(
                NDArrayIndex.all(),
                NDArrayIndex.all(),
                NDArrayIndex.interval(heightStart, heightStart + characterHeight),
                NDArrayIndex.interval(widthStart, widthStart + characterWidth)
        );
    }

    public String ocr() throws IOException {
        StringBuilder result = new StringBuilder();
        long num_row_chars = this.width / characterWidth;
        long num_column_chars = this.height / characterHeight;
        for (int height_index = 0; height_index < num_column_chars; height_index++){
            for (int width_index = 0; width_index < num_row_chars; width_index++){
                INDArray singleChar = this.cutChar(height_index, width_index);
                char c;
                try{
                    c = this.matchChar(singleChar);
                } catch (BrokenBitmapException e){
                    return "OCR: broken bitmap";
                }
                result.append(c);
            }
        }
        return result.toString();
    }

    public void save(Path p) throws IOException {
        Files.write(p, this.rawImage, StandardOpenOption.CREATE_NEW);
    }

}
