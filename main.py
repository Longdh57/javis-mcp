from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP(
    name="mcp-server",
    host="127.0.0.1",
    port=8000,
)


@mcp.custom_route("/", methods=["GET"])
async def root(request: Request) -> JSONResponse:
    return JSONResponse({"message": "MCP Server is running", "name": "mcp-server"})


@mcp.tool(description="Add two integers together and return the sum.")
def add(a: int, b: int) -> int:
    return a + b


@mcp.tool(description="Get the current temperature for a given city name. Returns temperature in Celsius.")
def get_current_temperature_by_city(city_name: str) -> str:
    return "20 degrees celsius"


@mcp.resource("resource://ma_so_thue", description="Returns the company tax identification number (mã số thuế).")
def get_ma_so_thue() -> str:
    return "1800278630"


@mcp.resource("resource://say_hi/{name}", description="Returns a greeting message for the given name.")
def say_hi(name: str) -> str:
    return f"Hello {name}"


@mcp.prompt(description="Generate a prompt to review a sentence and remove any personal information from it.")
def review_sentence(sentence: str) -> str:
    return f"Review this sentence, remove any personal information: \n\n{sentence}"


if __name__ == "__main__":
    # Run as streamable-http so Claude Terminal can connect via --transport http
    mcp.run(transport="streamable-http")
