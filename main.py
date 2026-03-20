import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP(
    name="javis-mcp-server",
    host="0.0.0.0",
    port=8000,
)

try:
    from trello_tools import register_trello_tools
    register_trello_tools(mcp)
except ImportError:
    print("trello_tools.py not found — run: python generate_trello_tools.py")

AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "123456789")  # Default token for testing, should be set in .env for production


class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/":
            return await call_next(request)
        if AUTH_TOKEN:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer ") or auth_header[7:] != AUTH_TOKEN:
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)


@mcp.custom_route("/", methods=["GET"])
async def root(request: Request) -> JSONResponse:
    return JSONResponse({"message": "Javis MCP Server is running", "name": "mcp-server"})


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
    app = mcp.streamable_http_app()
    app.add_middleware(TokenAuthMiddleware)
    uvicorn.run(app, host="0.0.0.0", port=8000)
