# ***** BEGIN LICENSE BLOCK *****
#
# For copyright and licensing please refer to COPYING.
#
# ***** END LICENSE BLOCK *****

import asyncore
import select
import socket
import time

from pika.adapters.base_connection import BaseConnection


class AsyncoreDispatcher(asyncore.dispatcher):
    """
    We extend asyncore.dispatcher here and throw in everything we need to
    handle both asyncore's needs and pika's. In the async adapter structure
    we expect a ioloop behavior which includes timeouts and a start and stop
    function.
    """

    def __init__(self, host, port):
        """
        Initialize the dispatcher, socket and our defaults. We turn of nageling
        in the socket to allow for faster throughput.
        """
        asyncore.dispatcher.__init__(self)

        # Create the socket, turn off nageling and connect
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.connect((host, port))

        # Setup defaults
        self.connecting = True
        self.connection = None
        self._timeouts = dict()
        self.writable_ = False
        self.map = None

    def handle_connect(self):
        """
        asyncore required method. Is called on connection.
        """
        self.connecting = False
        self.connection._on_connected()

        # Make our own map to pass in places
        self.map = dict({self.socket.fileno(): self})

    def handle_close(self):
        """
        asyncore required method. Is called on close.
        """
        # If we're not already closing or closed, disconnect the Connection
        if not self.connection.closing and not self.connection.closed:
            self.connection._adapter_disconnect()

    def handle_read(self):
        """
        Read from the socket and call our on_data_available with the data
        """
        try:
            data = self.recv(self.suggested_buffer_size)
        except socket.timeout:
            raise
        except socket.error, error:
            return self._handle_error(error)

        # We received no data, so disconnect
        if not data:
            return self.connection._adapter_disconnect()

        # Pass the data into our top level frame dispatching method
        self.connection._on_data_available(data)

    def handle_write(self):
        """
        asyncore required function, is called when we can write to the socket
        """
        data = self.connection.outbound_buffer.read(self.suggested_buffer_size)
        try:
            bytes_written = self.send(data)
        except socket.timeout:
            raise
        except socket.error, error:
            return self._handle_error(error)

        # Remove the content we used from our buffer
        if not bytes_written:
            return self.connection._adapter_disconnect()

        # Remove what we wrote from the outbound buffer
        self.connection.outbound_buffer.consume(bytes_written)

        # If our buffer is empty, turn off writing
        if not self.connection.outbound_buffer.size:
            self.writable_ = False

    def writable(self):
        """
        asyncore required function, used to toggle the write bit on the
        select poller. For some reason, if we return false while connecting
        asyncore hangs, so we check for that explicitly and tell it that
        it can write while it's connecting.
        """
        if not self.connected:
            return True

        # Flag maintained by AsyncoreConneciton.flush_outbound and
        # self.handle_write
        return self.writable_

    # IOLoop Compatibility
    def add_timeout(self, deadline, handler):
        """
        Add a timeout to the stack by deadline
        """
        timeout_id = 'id%.8f' % time.time()
        self._timeouts[timeout_id] = {'deadline': deadline,
                                      'handler': handler}
        return timeout_id

    def remove_timeout(self, timeout_id):
        """
        Remove a timeout from the stack
        """
        if timeout_id in self._timeouts:
            del self._timeouts[timeout_id]

    def _process_timeouts(self):
        """
        Process our self._timeouts event stack
        """
        # Process our timeout events
        keys = self._timeouts.keys()
        start_time = time.time()
        for timeout_id in keys:
            if timeout_id in self._timeouts and \
               self._timeouts[timeout_id]['deadline'] <= start_time:
                self._timeouts[timeout_id]['handler']()
                del(self._timeouts[timeout_id])

    def start(self):
        """
        Pika Adapter IOLoop start function. This blocks until we are no longer
        connected.
        """
        while self.connected or self.connecting:
            try:
                # Use our socket map if we've made it, makes things less buggy
                if self.map:
                    asyncore.loop(timeout=1, map=self.map, count=1)
                else:
                    asyncore.loop(timeout=1, count=1)
            except select.error, e:
                if e[0] == 9:
                    break
            self._process_timeouts()

    def stop(self):
        """
        Pika Adapter IOLoop stop function. When called, it will close an open
        connection, exiting us out of the IOLoop running in start.
        """
        self.close()


class AsyncoreConnection(BaseConnection):

    def _adapter_connect(self, host, port):
        """
        Connect to our RabbitMQ boker using AsyncoreDispatcher, then setting
        Pika's suggested buffer size for socket reading and writing. We pass
        the handle to self so that the AsyncoreDispatcher object can call back
        into our various state methods.
        """
        self.ioloop = AsyncoreDispatcher(host, port)

        # Map some core values for compatibility
        self.ioloop._handle_error = self._handle_error
        self.ioloop.connection = self
        self.ioloop.suggested_buffer_size = self._suggested_buffer_size
        self.socket = self.ioloop.socket

    def _flush_outbound(self):
        """
        We really can't flush the socket in asyncore, so instead just use this
        to toggle a flag that lets it know we want to write to the socket.
        """
        if self.outbound_buffer.size:
            self.ioloop.writable_ = True
