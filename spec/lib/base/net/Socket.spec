#! Package base:net
#! Network socket interface for TCP client and server communication.

Class is Socket{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', NetError],
		['base', 'struct', List],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Socket]
	];

	local Int is descriptor: -1;
	local Boolean is isClosed: true;

	local Function of Int is cstrAddr(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		return if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
	}

	## Reports a failure through [onError] as the full error currency:
	## a `SpecError of NetError` whose description carries the OS-level
	## error text.
	local Function is emitLastError(NetError is kind, Function is onError){
		local Int is errCstr: base:sysinternal:Socket:pal_socket_last_error();
		local String is msg: if({ errCstr != 0 }, {
			Mem:strFromBytes(srcAddr: errCstr, len: Mem:cstrLen(cstrAddr: errCstr))
		}, {
			'Socket error'
		});
		onError(SpecError:init(kind: kind, description: msg));
	}

	## Connects to a remote TCP server at [host]:[port].
	##
	## @param host: Target hostname or IP address.
	## @param port: Target TCP port number.
	## @param timeoutMs: Connection timeout in milliseconds (default 5000).
	## @param onError: Optional callback receiving the failure as the error currency
	## (`SpecError of NetError`).
	## @return: A new connected Socket instance, or nil/closed on failure.
	Function of Socket is connect(String is host, Int is port, Int is timeoutMs: 5000, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local Socket is s: Socket:init();
		local Int is fd: base:sysinternal:Socket:pal_tcp_connect(host_cstr: s:cstrAddr(s: host), port: port, timeout_ms: timeoutMs);
		if({ fd >= 0 }, {
			s:descriptor: fd;
			s:isClosed: false;
		}, {
			s:emitLastError(kind: NetError:CONNECT_FAILED, onError: onError);
		});
		return s;
	}

	## Binds and listens for incoming TCP connections on [port].
	##
	## @param host: Interface to bind (empty string for all interfaces).
	## @param port: TCP port to listen on.
	## @param backlog: Pending connection queue depth (default 128).
	## @param onError: Optional callback receiving the failure as the error currency
	## (`SpecError of NetError`).
	## @return: A listening Socket instance, or nil/closed on failure.
	Function of Socket is listen(String is host: '', Int is port, Int is backlog: 128, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local Socket is s: Socket:init();
		local Int is fd: base:sysinternal:Socket:pal_tcp_listen(host_cstr: s:cstrAddr(s: host), port: port, backlog: backlog);
		if({ fd >= 0 }, {
			s:descriptor: fd;
			s:isClosed: false;
		}, {
			s:emitLastError(kind: NetError:LISTEN_FAILED, onError: onError);
		});
		return s;
	}

	## Accepts an incoming connection on this listening socket.
	##
	## @param onError: Optional callback receiving the failure as the error currency
	## (`SpecError of NetError`).
	## @return: Connected client Socket instance.
	Function of Socket is accept(Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local Socket is client: Socket:init();
		local Int is clientFd: base:sysinternal:Socket:pal_socket_accept(fd: :descriptor);
		if({ clientFd >= 0 }, {
			client:descriptor: clientFd;
			client:isClosed: false;
		}, {
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
		});
		return client;
	}

	## Sends binary data from [data] over this socket.
	##
	## @param data: ByteBuffer with data to transmit.
	## @param onError: Optional callback receiving the failure as the error currency
	## (`SpecError of NetError`).
	## @return: Number of bytes sent, or -1 on error.
	Function of Int is send(List of Byte is data, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local Int is ptr: data:rawDataAddr();
		local Int is len: data:length();
		local Int is n: base:sysinternal:Socket:pal_socket_send(fd: :descriptor, data_addr: ptr, len: len);
		if({ n < 0 }, {
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
		});
		return n;
	}

	## Sends string text [text] over this socket.
	##
	## @param text: String to transmit.
	## @param onError: Optional callback receiving the failure as the error currency
	## (`SpecError of NetError`).
	## @return: Number of bytes sent, or -1 on error.
	Function of Int is sendString(String is text, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local Int is sAddr: Mem:objToAddr(obj: text);
		local Int is ptr: if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
		local Int is len: if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 8) }, { 0 });
		local Int is n: base:sysinternal:Socket:pal_socket_send(fd: :descriptor, data_addr: ptr, len: len);
		if({ n < 0 }, {
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
		});
		return n;
	}

	## Receives up to [maxBytes] into a new ByteBuffer.
	##
	## @param maxBytes: Maximum buffer size to read (default 4096).
	## @param onError: Optional callback receiving the failure as the error currency
	## (`SpecError of NetError`).
	## @return: Received ByteBuffer.
	Function of List of Byte is receive(Int is maxBytes: 4096, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local [Byte] is empty;
		if({ :isClosed }, {
			base:sysinternal:Socket:pal_socket_recv(fd: -1, dst_addr: 0, max_bytes: 0);
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
			return empty;
		});
		local Int is cap: maxBytes;
		if({ cap <= 0 }, { cap: 4096; });
		if({ cap > 1048576 }, { cap: 1048576; });
		local [Byte] is b;
		local Int is dataPtr: Mem:alloc(bytes: cap);
		local Int is n: base:sysinternal:Socket:pal_socket_recv(fd: :descriptor, dst_addr: dataPtr, max_bytes: cap);
		if({ n < 0 }, {
			Mem:free(ptr: dataPtr);
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
			return empty;
		});
		b:adoptRawBuffer(dataPtr: dataPtr, length: n, capacity: cap);
		return b;
	}

	## Receives up to [maxBytes] as a String.
	##
	## @param maxBytes: Maximum buffer size to read (default 4096).
	## @param onError: Optional callback receiving the failure as the error currency
	## (`SpecError of NetError`).
	## @return: Received String.
	Function of String is receiveString(Int is maxBytes: 4096, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local List of Byte is b: :receive(maxBytes: maxBytes, onError: onError);
		return b:toString();
	}

	## Polls the socket for I/O readiness.
	## Mode: 1=read, 2=write, 3=both.
	##
	## @param mode: Event mask to poll.
	## @param timeoutMs: Wait timeout in milliseconds (0 for non-blocking).
	## @return: true if ready for I/O.
	Function of Boolean is poll(Int is mode: 1, Int is timeoutMs: 0){
		if({ :isClosed }, {
			return false;
		});
		return base:sysinternal:Socket:socket_poll(fd: :descriptor, mode: mode, timeout_ms: timeoutMs) == 1;
	}

	## Sets socket send and receive timeout.
	##
	## @param timeoutMs: Timeout in milliseconds.
	## @return: true if successfully configured.
	Function of Boolean is setTimeout(Int is timeoutMs){
		if({ :isClosed }, {
			return false;
		});
		return base:sysinternal:Socket:socket_set_timeout(fd: :descriptor, timeout_ms: timeoutMs) == 0;
	}

	## Closes the socket connection.
	Function is close(){
		if({ !:isClosed }, {
			base:sysinternal:Socket:socket_close(fd: :descriptor);
			:isClosed: true;
			:descriptor: -1;
		});
	}

	## Returns the local bound port (useful after `listen(port: 0)`), or -1 if closed/error.
	Function of Int is localPort(){
		if({ :isClosed }, { return -1; });
		return base:sysinternal:Socket:pal_socket_local_port(fd: :descriptor);
	}

	## Returns true if the socket is open and connected.
	Function of Boolean is isOpen(){
		return !:isClosed;
	}

	held Function of Int is rawLastError(){
		return base:sysinternal:Socket:pal_socket_last_error();
	}

	held Function of Int is rawLocalPort(Int is fd){
		return base:sysinternal:Socket:pal_socket_local_port(fd: fd);
	}

	held Function of Int is rawUdpBind(Int is hostCstr, Int is port){
		return base:sysinternal:Socket:pal_udp_bind(host_cstr: hostCstr, port: port);
	}

	held Function of Int is rawUdpSendTo(Int is fd, Int is hostCstr, Int is port, Int is dataAddr, Int is len){
		return base:sysinternal:Socket:pal_udp_sendto(fd: fd, host_cstr: hostCstr, port: port, data_addr: dataAddr, len: len);
	}

	held Function of Int is rawUdpRecvFrom(Int is fd, Int is dstAddr, Int is maxBytes, Int is hostBuf, Int is hostBufLen, Int is portOutAddr){
		return base:sysinternal:Socket:pal_udp_recvfrom(fd: fd, dst_addr: dstAddr, max_bytes: maxBytes, host_buf: hostBuf, host_buf_len: hostBufLen, port_out_addr: portOutAddr);
	}

	held Function of Int is rawPoll(Int is fd, Int is mode, Int is timeoutMs){
		return base:sysinternal:Socket:socket_poll(fd: fd, mode: mode, timeout_ms: timeoutMs);
	}

	held Function of Int is rawSetTimeout(Int is fd, Int is timeoutMs){
		return base:sysinternal:Socket:socket_set_timeout(fd: fd, timeout_ms: timeoutMs);
	}

	held Function of Int is rawClose(Int is fd){
		return base:sysinternal:Socket:socket_close(fd: fd);
	}
}
