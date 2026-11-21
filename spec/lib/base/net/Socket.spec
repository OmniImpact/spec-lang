#! Package base:net
#! Network socket interface for TCP client and server communication.

Class is Socket{
	namespace: ['base', 'net'];

	replace Array of Array of String is using: [
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
		local Int is bAddr: Mem:objToAddr(obj: data);
		local Int is ptr: if({ bAddr != 0 }, { Mem:loadI64(ptr: bAddr, byteOffset: 0) }, { 0 });
		local Int is len: if({ bAddr != 0 }, { Mem:loadI64(ptr: bAddr, byteOffset: 8) }, { 0 });
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
		local Int is bAddr: Mem:objToAddr(obj: b);
		local Int is dataPtr: Mem:alloc(bytes: cap);
		Mem:storeI64(ptr: bAddr, byteOffset: 0, val: dataPtr);
		Mem:storeI64(ptr: bAddr, byteOffset: 16, val: cap);
		local Int is n: base:sysinternal:Socket:pal_socket_recv(fd: :descriptor, dst_addr: dataPtr, max_bytes: cap);
		if({ n < 0 }, {
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
			return empty;
		});
		Mem:storeI64(ptr: bAddr, byteOffset: 8, val: n);
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

	## Returns true if the socket is open and connected.
	Function of Boolean is isOpen(){
		return !:isClosed;
	}
}
