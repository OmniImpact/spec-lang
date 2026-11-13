#! Package base:sysinternal
#! The socket floor: low-level networking primitives bound to C.

Class is Socket{
	namespace: ['base', 'sysinternal'];

	## Connects to [host] on [port] via TCP. Bound to `spec_tcp_connect`.
	##
	## @param host: Target host name or IP address.
	## @param port: Target TCP port number.
	## @param timeout_ms: Connection timeout in milliseconds (0 for default).
	## @return: Socket file descriptor, or -1 on error.
	Function of Int is tcp_connect(String is host, Int is port, Int is timeout_ms);

	## Binds and listens on [port] for incoming TCP connections. Bound to `spec_tcp_listen`.
	##
	## @param host: Interface to bind (empty string or "0.0.0.0" for any).
	## @param port: TCP port number to listen on.
	## @param backlog: Queue depth for pending connections (default 128).
	## @return: Listening socket file descriptor, or -1 on error.
	Function of Int is tcp_listen(String is host, Int is port, Int is backlog);

	## Accepts an incoming connection on [fd]. Bound to `spec_socket_accept`.
	##
	## @param fd: Listening socket descriptor.
	## @return: Connected client socket descriptor, or -1 on error.
	Function of Int is socket_accept(Int is fd);

	## Sends [data] over socket [fd]. Bound to `spec_socket_send`.
	##
	## @param fd: Connected socket descriptor.
	## @param data: ByteBuffer containing payload.
	## @return: Number of bytes sent, or -1 on error.
	Function of Int is socket_send(Int is fd, ByteBuffer is data);

	## Sends string [str] over socket [fd]. Bound to `spec_socket_send_str`.
	##
	## @param fd: Connected socket descriptor.
	## @param str: String payload.
	## @return: Number of bytes sent, or -1 on error.
	Function of Int is socket_send_str(Int is fd, String is str);

	## Receives up to [max_bytes] from socket [fd]. Bound to `spec_socket_recv`.
	##
	## @param fd: Connected socket descriptor.
	## @param max_bytes: Maximum chunk size to read.
	## @return: Received ByteBuffer, empty on EOF, or empty on error.
	Function of ByteBuffer is socket_recv(Int is fd, Int is max_bytes);

	## Receives up to [max_bytes] as a String from socket [fd]. Bound to `spec_socket_recv_str`.
	##
	## @param fd: Connected socket descriptor.
	## @param max_bytes: Maximum chunk size to read.
	## @return: Received String, or empty string on EOF/error.
	Function of String is socket_recv_str(Int is fd, Int is max_bytes);

	## Closes socket [fd]. Bound to `spec_socket_close`.
	##
	## @param fd: Socket descriptor to close.
	## @return: 0 on success.
	Function of Int is socket_close(Int is fd);

	## Polls [fd] for readiness. Bound to `spec_socket_poll`.
	## Mode: 1=read, 2=write, 3=both.
	##
	## @param fd: Socket descriptor.
	## @param mode: Bitmask of events to poll.
	## @param timeout_ms: Timeout in milliseconds.
	## @return: 1 if ready, 0 if timed out, -1 on error.
	Function of Int is socket_poll(Int is fd, Int is mode, Int is timeout_ms);

	## Configures send and receive timeout on [fd]. Bound to `spec_socket_set_timeout`.
	##
	## @param fd: Socket descriptor.
	## @param timeout_ms: Timeout duration in milliseconds.
	## @return: 0 on success, -1 on error.
	Function of Int is socket_set_timeout(Int is fd, Int is timeout_ms);
}
