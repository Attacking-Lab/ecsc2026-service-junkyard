
struct Meta
    op::UInt8
    i1::UInt16
    i2::UInt16
    i3::UInt16
    i4::UInt16
    s1::String
end


function parse_meta(filename::String)::Array{Meta}
    result = Meta[]
    f = open(filename, "r")
    try
        while !eof(f)
            op = unpack(f, UInt8)
            if op == 1
                l = unpack(f, UInt8)
                s = read(f, l)
                push!(result, Meta(op, 0, 0, 0, 0, String(s)))
            elseif op == 2
                push!(result, Meta(op, 0, 0, 0, 0, ""))
            elseif op == 3 || op == 4
                i1 = unpack(f, UInt16)
                i2 = unpack(f, UInt16)
                i3 = unpack(f, UInt16)
                i4 = unpack(f, UInt16)
                push!(result, Meta(op, i1, i2, i3, i4, ""))
            else
                break
            end
        end
    finally
        close(f)
    end
    return result
end


function allow_action(metadata::Array{Meta}, username::String)::Bool
    if length(metadata) >= 8
        return false
    end
    for meta in metadata
        if meta.op == 0x1 && meta.s1 == username
            return true
        end
        if meta.op == 0x2
            return true
        end
    end
    return false
end
