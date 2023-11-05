import uasyncio as asyncio
import usocket as socket

async def handle_client(reader, writer):
    request = await reader.read(1024)
    response = """HTTP/1.1 200 OK
Content-Type: text/html

<html><body><h1>Hello, MicroPython!</h1></body></html>
"""
    await writer.awrite(response)
    await writer.aclose()

async def web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print('Listening on', addr)

    while True:
        client, addr = await asyncio.start_server(handle_client, '0.0.0.0', 80)
        asyncio.create_task(handle_client(client, addr))

def start_web_server():
    asyncio.run(web_server())

# Then, in your main code:
start_web_server()
In your main application loop, if you have any tasks that might take some time and you want to make sure they don't block the web server for too long, you can sprinkle in occasional short uasyncio.sleep() calls to yield back to the event loop.
For instance:

python
Copy code
async def main_task():
    while True:
        # Do some work
        await asyncio.sleep(0.1)  # This gives a chance for the web server to handle requests.

asyncio.create_task(main_task())
By creating and starting the web server as an asynchronous task, it runs 'concurrently' with your main application loop. Using uasyncio.sleep() strategically will ensure that the web server gets time slices to handle incoming requests even if your main loop is busy.

This approach leverages the cooperative multitasking nature of uasyncio without forcing you to refactor your entire application to be non-blocking.





