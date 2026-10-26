module Inspector

include("server.jl")

# julia --project=. -m Inspector

function @main(args::Vector{String})::Cint
    routing = get_server()
    try
        HTTP.serve(routing, "0.0.0.0", 9301, reuseaddr=true)
    catch e
        if e isa InterruptException
        else
            rethrow()
        end
    end
    return 0
end

end