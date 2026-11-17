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

	## Connects to [host] on [port] via TCP, invoking [on_error] on failure.
	## Bound to `spec_tcp_connect_cb`.
	Function of Int is tcp_connect_cb(String is host, Int is port, Int is timeout_ms, Function is on_error);

	## Binds and listens on [port] for incoming TCP connections. Bound to `spec_tcp_listen`.
	##
	## @param host: Interface to bind (empty string or "0.0.0.0" for any).
	## @param port: TCP port number to listen on.
	## @param backlog: Queue depth for pending connections (default 128).
	## @return: Listening socket file descriptor, or -1 on error.
	Function of Int is tcp_listen(String is host, Int is port, Int is backlog);

	## Binds and listens on [port], invoking [on_error] on failure.
	## Bound to `spec_tcp_listen_cb`.
	Function of Int is tcp_listen_cb(String is host, Int is port, Int is backlog, Function is on_error);

	## Accepts an incoming connection on [fd]. Bound to `spec_socket_accept`.
	##
	## @param fd: Listening socket descriptor.
	## @return: Connected client socket descriptor, or -1 on error.
	Function of Int is socket_accept(Int is fd);

	## Accepts an incoming connection on [fd], invoking [on_error] on failure.
	## Bound to `spec_socket_accept_cb`.
	Function of Int is socket_accept_cb(Int is fd, Function is on_error);

	## Sends [len] bytes at [data_addr] over socket [fd], invoking [on_error] on failure.
	## Bound to `spec_pal_socket_send`.
	Function of Int is pal_socket_send(Int is fd, Int is data_addr, Int is len, Function is on_error);

	## Sends string [str] over socket [fd]. Bound to `spec_socket_send_str`.
	##
	## @param fd: Connected socket descriptor.
	## @param str: String payload.
	## @return: Number of bytes sent, or -1 on error.
	Function of Int is socket_send_str(Int is fd, String is str);

	## Sends string [str] over socket [fd], invoking [on_error] on failure.
	## Bound to `spec_socket_send_str_cb`.
	Function of Int is socket_send_str_cb(Int is fd, String is str, Function is on_error);

	## Receives up to [max_bytes] into [dst_addr] from socket [fd], invoking [on_error] on failure.
	## Bound to `spec_pal_socket_recv`.
	Function of Int is pal_socket_recv(Int is fd, Int is dst_addr, Int is max_bytes, Function is on_error);

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
