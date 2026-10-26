using HTTP

include("ops.jl")


function process_file(req::HTTP.Request)::HTTP.Response
    FILE_BASE = get(ENV, "FILE_DIR", "service/gateway/data/files")

    params = HTTP.queryparams(HTTP.URI(req.target).query)
    if !haskey(params, "filename") || !haskey(params, "meta") || !haskey(params, "username")
        return HTTP.Response(400, "params missing")
    end

    try
        image::Bitmap = load_bitmap(FILE_BASE * "/" * params["filename"] * "/data.bmp")
        metas::Vector{Meta} = parse_meta(FILE_BASE * "/" * params["filename"] * "/" * params["meta"] * ".meta")

        if !allow_action(metas, params["username"])
            return HTTP.Response(403, "Not permitted to access this junk")
        end
        
        output_image = apply_meta_to_image(image, metas)
        return HTTP.Response(200, bitmap_to_bytes(output_image))

    catch e
        if isa(e, DomainError)
            return HTTP.Response(400, "Error: $(typeof(e)) $e")
        else
            println(e)
            return HTTP.Response(400, "Error: $(typeof(e))")
        end
    end
end


_404(req) = HTTP.Response(404, "nothing here!")


function get_server()
    router = HTTP.Router(_404)
    routing(req) = router(req)
    HTTP.register!(router, "POST", "/process", process_file)
    return routing
end
