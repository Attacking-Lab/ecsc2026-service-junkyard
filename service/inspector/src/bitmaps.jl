using StructIO


a ↦ b = a:b-1


@io struct BmpHeader
    magic_number::UInt16
    size::UInt32
    reserved1::UInt16
    reserved2::UInt16
    offset::UInt32
    dib_header_size::UInt32
    width::Int32
    height::Int32
    color_planes::UInt16
    bits_per_pixel::UInt16
    compression_method::UInt32
end align_packed


struct Bitmap
    header::BmpHeader
    data::Vector{UInt8}
end


function bytes_to_struct(T, data::Vector{UInt8}, offset::Int)::T
    buffer = IOBuffer(data)
    seek(buffer, offset)
    return unpack(buffer, T, :LittleEndian)
end


function load_bitmap(filename::String)::Bitmap
    n = filesize(filename)
    data = Vector{UInt8}(undef, n)
    fᵢₙ = open(filename, "r")
    readbytes!(fᵢₙ, data, all=true)
    close(fᵢₙ)

    header::BmpHeader = bytes_to_struct(BmpHeader, data, 0)
    if header.magic_number != 0x4d42
        throw(DomainError(header, "This is not a bmp"))
    end
    if header.color_planes != 1 || header.bits_per_pixel != 32 || (header.compression_method != 3 && header.compression_method != 0)
        throw(DomainError(header, "Invalid bmp format, please use 32bit uncompressed bmps"))
    end
    if header.width > 1250 || header.height > 1250
        throw(DomainError(header, "Bitmap too large"))
    end

    return Bitmap(header, data)
end


function save_bitmap(filename::String, bitmap::Bitmap)
    fₒᵤₜ = open(filename, "w")
    write(fₒᵤₜ, bitmap.data)
    close(fₒᵤₜ)
end


function bitmap_to_bytes(bitmap::Bitmap)::Vector{UInt8}
    return bitmap.data
end


function clone(bmp::Bitmap)::Bitmap
    return Bitmap(bmp.header, bmp.data[:])
end


function new_from_template(bmp::Bitmap, new_width::Int32, new_height::Int32)::Bitmap
    new_header = BmpHeader(
        bmp.header.magic_number,
        bmp.header.size - bmp.header.width * bmp.header.height * 4 + new_width * new_height * 4,
        bmp.header.reserved1,
        bmp.header.reserved2,
        bmp.header.offset,
        bmp.header.dib_header_size,
        new_width,
        new_height,
        bmp.header.color_planes,
        bmp.header.bits_per_pixel,
        bmp.header.compression_method
    )

    data = Vector{UInt8}(undef, bmp.header.offset + new_width * new_height * 4)
    header_buf = IOBuffer(sizehint = 34)
    pack(header_buf, new_header, :LittleEndian)
    copyto!(data, 1, take!(header_buf), 1, 34)
    copyto!(data, 35, bmp.data, 35, bmp.header.offset - 34)

    return Bitmap(new_header, data)
end


@inline function idx(bmp::Bitmap, x::Int, y::Int, channel::Int)::Int64
    if x < 0
        x = 0
    end
    if x ≥ bmp.header.width
        x = bmp.header.width - 1
    end
    if y < 0
        y = 0
    end
    if y ≥ bmp.header.height
        y = bmp.header.height - 1
    end
    return bmp.header.offset + (y * bmp.header.width + x) * 4 + channel
end
