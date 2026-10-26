include("bitmaps.jl")
include("meta.jl")

@inline function idx_xy(bmp::Bitmap, x::Int, y::Int, channel::Int)::Int64
    return idx(bmp, x, bmp.header.height - y, channel)
end


function blackout!(bmp::Bitmap, x, y, w, h)
    if x < 0
        x = 0
    end
    if y < 0
        y = 0
    end
    if x+w > bmp.header.width
        w = bmp.header.width - x
    end
    if y+h > bmp.header.height
        h = bmp.header.height - y
    end

    for row in (y ↦ y + h)
        for col in (x ↦ x + w)
            bmp.data[idx_xy(bmp, col, row, 1)] = 0
            bmp.data[idx_xy(bmp, col, row, 2)] = 0
            bmp.data[idx_xy(bmp, col, row, 3)] = 0
            bmp.data[idx_xy(bmp, col, row, 4)] = 255
        end
    end
end


function crop(bmp::Bitmap, t, r, b, l)::Bitmap
    out::Bitmap = new_from_template(bmp, bmp.header.width - l - r, bmp.header.height - t - b)

    for y in (b ↦ bmp.header.height - t)
        for x in (l ↦ bmp.header.width - r)
            copyto!(out.data, idx(out, x - l, y - b, 1), bmp.data, idx(bmp, x, y, 1), 4)
        end
    end

    return out
end


function apply_meta_to_image(image::Bitmap, metadata::Vector{Meta})::Bitmap
    for meta in metadata
        if meta.op == 0x3
            image = crop(image, meta.i1, meta.i2, meta.i3, meta.i4)
        end
    end

    for meta in metadata
        if meta.op == 0x4
            blackout!(image, meta.i1, meta.i2, meta.i3, meta.i4)
        end
    end

    return image
end
