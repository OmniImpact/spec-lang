#! Package base:net
#! Network socket interface for TCP client and server communication.

Class is Socket{
	namespace: ['base', 'net'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Socket]
	];

	local Int is descriptor: -1;
	local Boolean is isClosed: true;

	## Connects to a remote TCP server at [host]:[port].
	##
	## @param host: Target hostname or IP address.
	## @param port: Target TCP port number.
	## @param timeoutMs: Connection timeout in milliseconds (default 5000).
	## @return: A new connected Socket instance, or nil/closed on failure.
	Function of Socket is connect(String is host, Int is port, Int is timeoutMs: 5000){
		local Socket is s: Socket:init();
		local Int is fd: base:sysinternal:Socket:tcp_connect(host: host, port: port, timeout_ms: timeoutMs);
		if({ fd >= 0 }, {
			s:descriptor: fd;
			s:isClosed: false;
		});
		return s;
	}

	## Binds and listens for incoming TCP connections on [port].
	##
	## @param host: Interface to bind (empty string for all interfaces).
	## @param port: TCP port to listen on.
	## @param backlog: Pending connection queue depth (default 128).
	## @return: A listening Socket instance, or nil/closed on failure.
	Function of Socket is listen(String is host: '', Int is port, Int is backlog: 128){
		local Socket is s: Socket:init();
		local Int is fd: base:sysinternal:Socket:tcp_listen(host: host, port: port, backlog: backlog);
		if({ fd >= 0 }, {
			s:descriptor: fd;
			s:isClosed: false;
		});
		return s;
	}

	## Accepts an incoming connection on this listening socket.
	##
	## @return: Connected client Socket instance.
	Function of Socket is accept(){
		local Socket is client: Socket:init();
		if({ self:isClosed }, {
			return client;
		});
		local Int is clientFd: base:sysinternal:Socket:socket_accept(fd: self:descriptor);
		if({ clientFd >= 0 }, {
			client:descriptor: clientFd;
			client:isClosed: false;
		});
		return client;
	}

	## Sends binary data from [data] over this socket.
	##
	## @param data: ByteBuffer with data to transmit.
	## @return: Number of bytes sent, or -1 on error.
	Function of Int is send(ByteBuffer is data){
		if({ self:isClosed }, {
			return -1;
		});
		return base:sysinternal:Socket:socket_send(fd: self:descriptor, data: data);
	}

	## Sends string text [text] over this socket.
	##
	## @param text: String to transmit.
	## @return: Number of bytes sent, or -1 on error.
	Function of Int is sendString(String is text){
		if({ self:isClosed }, {
			return -1;
		});
		return base:sysinternal:Socket:socket_send_str(fd: self:descriptor, str: text);
	}

	## Receives up to [maxBytes] into a new ByteBuffer.
	##
	## @param maxBytes: Maximum buffer size to read (default 4096).
	## @return: Received ByteBuffer.
	Function of ByteBuffer is receive(Int is maxBytes: 4096){
		if({ self:isClosed }, {
			return ByteBuffer:init();
		});
		return base:sysinternal:Socket:socket_recv(fd: self:descriptor, max_bytes: maxBytes);
	}

	## Receives up to [maxBytes] as a String.
	##
	## @param maxBytes: Maximum buffer size to read (default 4096).
	## @return: Received String.
	Function of String is receiveString(Int is maxBytes: 4096){
		if({ self:isClosed }, {
			return '';
		});
		return base:sysinternal:Socket:socket_recv_str(fd: self:descriptor, max_bytes: maxBytes);
	}

	## Polls the socket for I/O readiness.
	## Mode: 1=read, 2=write, 3=both.
	##
	## @param mode: Event mask to poll.
	## @param timeoutMs: Wait timeout in milliseconds (0 for non-blocking).
	## @return: true if ready for I/O.
	Function of Boolean is poll(Int is mode: 1, Int is timeoutMs: 0){
		if({ self:isClosed }, {
			return false;
		});
		return base:sysinternal:Socket:socket_poll(fd: self:descriptor, mode: mode, timeout_ms: timeoutMs) == 1;
	}

	## Sets socket send and receive timeout.
	##
	## @param timeoutMs: Timeout in milliseconds.
	## @return: true if successfully configured.
	Function of Boolean is setTimeout(Int is timeoutMs){
		if({ self:isClosed }, {
			return false;
		});
		return base:sysinternal:Socket:socket_set_timeout(fd: self:descriptor, timeout_ms: timeoutMs) == 0;
	}

	## Closes the socket connection.
	Function is close(){
		if({ !self:isClosed }, {
			base:sysinternal:Socket:socket_close(fd: self:descriptor);
			self:isClosed: true;
			self:descriptor: -1;
		});
	}

	## Returns true if the socket is open and connected.
	Function of Boolean is isOpen(){
		return !self:isClosed;
	}
}
