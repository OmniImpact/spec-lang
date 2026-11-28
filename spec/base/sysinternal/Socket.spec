#! Package base:sysinternal
#! The socket floor: low-level networking primitives bound to C.

Class is Socket{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Returns the C-string address of the last socket error on this thread.
	## Bound to `spec_pal_socket_last_error`.
	Function of Int is pal_socket_last_error();

	## Connects to C-string [host_cstr] on [port] via TCP.
	## Bound to `spec_pal_tcp_connect`.
	Function of Int is pal_tcp_connect(Int is host_cstr, Int is port, Int is timeout_ms);

	## Binds and listens on [port] for incoming TCP connections.
	## Bound to `spec_pal_tcp_listen`.
	Function of Int is pal_tcp_listen(Int is host_cstr, Int is port, Int is backlog);

	## Accepts an incoming connection on [fd].
	## Bound to `spec_pal_socket_accept`.
	Function of Int is pal_socket_accept(Int is fd);

	## Sends [len] bytes at [data_addr] over socket [fd].
	## Bound to `spec_pal_socket_send`.
	Function of Int is pal_socket_send(Int is fd, Int is data_addr, Int is len);

	## Receives up to [max_bytes] into [dst_addr] from socket [fd].
	## Bound to `spec_pal_socket_recv`.
	Function of Int is pal_socket_recv(Int is fd, Int is dst_addr, Int is max_bytes);

	## Closes socket [fd]. Bound to `spec_socket_close`.
	Function of Int is socket_close(Int is fd);

	## Polls [fd] for readiness. Bound to `spec_socket_poll`.
	## Mode: 1=read, 2=write, 3=both.
	Function of Int is socket_poll(Int is fd, Int is mode, Int is timeout_ms);

	## Configures send and receive timeout on [fd]. Bound to `spec_socket_set_timeout`.
	Function of Int is socket_set_timeout(Int is fd, Int is timeout_ms);

	## Returns the local bound port of [fd] via getsockname, or -1 on error.
	## Bound to `spec_pal_socket_local_port`.
	Function of Int is pal_socket_local_port(Int is fd);

	## Binds a UDP (SOCK_DGRAM) socket to [host_cstr]:[port] (port 0 = ephemeral).
	## Bound to `spec_pal_udp_bind`.
	Function of Int is pal_udp_bind(Int is host_cstr, Int is port);

	## Sends a UDP datagram to [host_cstr]:[port].
	## Bound to `spec_pal_udp_sendto`.
	Function of Int is pal_udp_sendto(Int is fd, Int is host_cstr, Int is port, Int is data_addr, Int is len);

	## Receives a UDP datagram into [dst_addr], writing peer IP C-string and port.
	## Bound to `spec_pal_udp_recvfrom`.
	Function of Int is pal_udp_recvfrom(Int is fd, Int is dst_addr, Int is max_bytes, Int is host_buf, Int is host_buf_len, Int is port_out_addr);
}
