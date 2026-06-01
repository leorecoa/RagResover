const http = require("http");
const fs = require("fs");
const path = require("path");

const port = Number(process.env.PORT || 3000);
const root = path.resolve(__dirname);

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

function send(response, statusCode, body, contentType = "text/plain; charset=utf-8") {
  response.writeHead(statusCode, {
    "Content-Type": contentType,
    "Cache-Control": "no-store",
  });
  response.end(body);
}

function resolveRequestPath(url) {
  const requestUrl = new URL(url, `http://localhost:${port}`);
  const pathname = requestUrl.pathname === "/" ? "index.html" : requestUrl.pathname.replace(/^\/+/, "");
  const filePath = path.resolve(root, pathname);
  const relativePath = path.relative(root, filePath);

  if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
    return null;
  }

  return filePath;
}

const server = http.createServer((request, response) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    response.setHeader("Allow", "GET, HEAD");
    send(response, 405, "Method not allowed");
    return;
  }

  const filePath = resolveRequestPath(request.url);
  if (!filePath) {
    send(response, 403, "Forbidden");
    return;
  }

  fs.readFile(filePath, (error, data) => {
    if (error) {
      send(response, 404, "Not found");
      return;
    }

    const contentType = contentTypes[path.extname(filePath)] || "application/octet-stream";
    send(response, 200, request.method === "HEAD" ? "" : data, contentType);
  });
});

server.listen(port, "127.0.0.1", () => {
  console.log(`RagResover frontend: http://127.0.0.1:${port}`);
});
