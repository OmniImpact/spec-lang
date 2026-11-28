#! Package base:net
#! UDP datagram socket over `base:net:Socket` floor wrappers.

Class is UdpSocket{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', NetError],
		['base', 'net', Socket],
		['base', 'net', UdpPacket],
		['base', 'struct', List],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()]
	];

	local Int is descriptor: -1;
	local Boolean is isClosed: true;

	local Function of Int is cstrAddr(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		if({ sAddr == 0 || Mem:loadI64(ptr: sAddr, byteOffset: 8) == 0 }, {
			return 0;
		});
		return Mem:loadI64(ptr: sAddr, byteOffset: 0);
	}

	local Function is emitLastError(NetError is kind, Function is onError){
		if({ !Mem:hasClosure(cb: onError) }, { return; });
		local Int is errPtr: Socket:rawLastError();
		local String is msg: 'UDP socket error';
		if({ errPtr != 0 }, {
			local Int is n: 0;
			while({ Mem:loadByte(ptr: errPtr, byteOffset: n) != 0 }, { n: n + 1; });
			if({ n > 0 }, { msg: Mem:strFromBytes(srcAddr: errPtr, len: n); });
		});
		onError(SpecError:init(kind: kind, description: msg));
	}

	## Binds a UDP socket to [host]:[port] (`port: 0` requests an ephemeral OS port).
	Function of UdpSocket is bind(String is host: '0.0.0.0', Int is port: 0, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local UdpSocket is s: UdpSocket:init();
		local Int is fd: Socket:rawUdpBind(hostCstr: s:cstrAddr(s: host), port: port);
		if({ fd < 0 }, {
			s:emitLastError(kind: NetError:LISTEN_FAILED, onError: onError);
			return s;
		});
		s:descriptor: fd;
		s:isClosed: false;
		return s;
	}

	## Returns the local bound port (useful after `bind(port: 0)`), or -1 if closed.
	Function of Int is localPort(){
		if({ :isClosed }, { return -1; });
		return Socket:rawLocalPort(fd: :descriptor);
	}

	## Sends raw bytes [data] to [host]:[port].
	Function of Int is sendTo(String is host, Int is port, List of Byte is data, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		if({ :isClosed }, {
			if({ Mem:hasClosure(cb: onError) }, { onError(SpecError:init(kind: NetError:IO_ERROR, description: 'UDP socket is closed')); });
			return -1;
		});
		local Int is len: data:length();
		if({ len <= 0 }, { return 0; });
		local Int is sent: Socket:rawUdpSendTo(fd: :descriptor, hostCstr: :cstrAddr(s: host), port: port, dataAddr: data:rawDataAddr(), len: len);
		if({ sent < 0 }, {
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
		});
		return sent;
	}

	## Sends UTF-8 [text] to [host]:[port].
	Function of Int is sendStringTo(String is host, Int is port, String is text, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		if({ :isClosed }, {
			if({ Mem:hasClosure(cb: onError) }, { onError(SpecError:init(kind: NetError:IO_ERROR, description: 'UDP socket is closed')); });
			return -1;
		});
		local Int is sAddr: Mem:objToAddr(obj: text);
		if({ sAddr == 0 }, { return 0; });
		local Int is dataPtr: Mem:loadI64(ptr: sAddr, byteOffset: 0);
		local Int is len: Mem:loadI64(ptr: sAddr, byteOffset: 8);
		if({ len <= 0 }, { return 0; });
		local Int is sent: Socket:rawUdpSendTo(fd: :descriptor, hostCstr: :cstrAddr(s: host), port: port, dataAddr: dataPtr, len: len);
		if({ sent < 0 }, {
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
		});
		return sent;
	}

	## Receives up to [maxBytes] into a [UdpPacket] with peer `host` and `port`.
	Function of UdpPacket is receiveFrom(Int is maxBytes: 4096, Function is onError: local Function(SpecError of NetError is error){ :raiseError(error: error); }){
		local List of Byte is empty;
		if({ :isClosed }, {
			if({ Mem:hasClosure(cb: onError) }, { onError(SpecError:init(kind: NetError:IO_ERROR, description: 'UDP socket is closed')); });
			return UdpPacket:init(data: empty, host: '', port: 0, length: -1);
		});
		local Int is cap: if({ maxBytes > 0 }, { maxBytes }, { 4096 });
		local Int is dataPtr: Mem:alloc(bytes: cap);
		local Int is hostBuf: Mem:alloc(bytes: 64);
		local Int is portBox: Mem:alloc(bytes: 8);
		Mem:storeI64(ptr: portBox, byteOffset: 0, val: 0);
		local Int is n: Socket:rawUdpRecvFrom(fd: :descriptor, dstAddr: dataPtr, maxBytes: cap, hostBuf: hostBuf, hostBufLen: 64, portOutAddr: portBox);
		local Int is peerPort: Mem:loadI64(ptr: portBox, byteOffset: 0);
		local String is peerHost: '';
		if({ n >= 0 }, {
			local Int is hLen: 0;
			while({ hLen < 63 && Mem:loadByte(ptr: hostBuf, byteOffset: hLen) != 0 }, { hLen: hLen + 1; });
			if({ hLen > 0 }, { peerHost: Mem:strFromBytes(srcAddr: hostBuf, len: hLen); });
		});
		Mem:free(ptr: hostBuf);
		Mem:free(ptr: portBox);
		if({ n < 0 }, {
			Mem:free(ptr: dataPtr);
			:emitLastError(kind: NetError:IO_ERROR, onError: onError);
			return UdpPacket:init(data: empty, host: '', port: 0, length: -1);
		});
		local List of Byte is payload;
		payload:adoptRawBuffer(dataPtr: dataPtr, length: n, capacity: cap);
		return UdpPacket:init(data: payload, host: peerHost, port: peerPort, length: n);
	}

	Function of Boolean is poll(Int is mode: 1, Int is timeoutMs: 0){
		if({ :isClosed }, { return false; });
		return Socket:rawPoll(fd: :descriptor, mode: mode, timeoutMs: timeoutMs) == 1;
	}

	Function of Boolean is setTimeout(Int is timeoutMs){
		if({ :isClosed }, { return false; });
		return Socket:rawSetTimeout(fd: :descriptor, timeoutMs: timeoutMs) == 0;
	}

	Function is close(){
		if({ !:isClosed }, {
			Socket:rawClose(fd: :descriptor);
			:isClosed: true;
			:descriptor: -1;
		});
	}

	Function of Boolean is isOpen(){
		return !:isClosed;
	}
}
