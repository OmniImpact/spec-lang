#! Package base:net
#! RFC 6455 WebSocket client/server upgrade handshake and text/binary framing over `Socket`.

Class is WebSocket{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', Socket],
		['base', 'net', NetError],
		['base', 'math', 'crypto', as Sha1()],
		['base', 'math', 'crypto', as Pem()],
		['base', 'struct', Array],
		['base', 'struct', List],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()]
	];

	local Socket is sock: Socket:init();
	local Boolean is isClient: true;
	local Boolean is open: false;

	replace Function is init(){
		:sock: Socket:init();
		:isClient: true;
		:open: false;
	}

	## Computes the RFC 6455 `Sec-WebSocket-Accept` header value for [clientKey].
	Function of String is computeAcceptKey(String is clientKey){
		local Array of Int is hash: Sha1:digestString(text: clientKey:trim() . '258EAFA5-E914-47DA-95CA-C5AB0DC85B11');
		return Pem:base64Encode(data: hash);
	}

	## Connects as a WebSocket client to `ws://[host]:[port][path]`.
	Function of Boolean is connect(String is host, Int is port: 80, String is path: '/', Int is timeoutMs: 10000){
		local Boolean is err: false;
		:sock: Socket:init():connect(host: host, port: port, timeoutMs: timeoutMs, onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err || !:sock:isOpen() }, { return false; });
		:sock:setTimeout(timeoutMs: timeoutMs);
		local String is wsKey: 'dGhlIHNhbXBsZSBub25jZQ==';
		local String is req: 'GET ' . path . " HTTP/1.1\r\n"
			. 'Host: ' . host . ':' . (port as String) . "\r\n"
			. "Upgrade: websocket\r\n"
			. "Connection: Upgrade\r\n"
			. 'Sec-WebSocket-Key: ' . wsKey . "\r\n"
			. "Sec-WebSocket-Version: 13\r\n\r\n";
		:sock:sendString(text: req, onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err }, { :sock:close(); return false; });

		local String is resp: :sock:receiveString(maxBytes: 4096, onError: local Function(SpecError of NetError is _e){ err: true; });
		local String is expectedAccept: :computeAcceptKey(clientKey: wsKey);
		if({ err || !resp:contains(needle: '101') || !resp:contains(needle: expectedAccept) }, {
			:sock:close();
			return false;
		});
		:isClient: true;
		:open: true;
		return true;
	}

	## Accepts an incoming TCP [clientSocket] and performs the RFC 6455 server upgrade handshake.
	Function of Boolean is acceptHandshake(Socket is clientSocket, Int is timeoutMs: 10000){
		:sock: clientSocket;
		:sock:setTimeout(timeoutMs: timeoutMs);
		local Boolean is err: false;
		local String is req: :sock:receiveString(maxBytes: 4096, onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err || req:byteLength() == 0 }, { :sock:close(); return false; });
		local String is low: req:toLower();
		local Int is kIdx: low:indexOf(search: 'sec-websocket-key:', default: -1);
		if({ kIdx < 0 }, { :sock:close(); return false; });
		local Int is vStart: kIdx + 18;
		local Int is vEnd: req:indexOfFrom(search: "\r\n", from: vStart, default: req:length());
		local String is clientKey: req:substring(start: vStart, end: vEnd):trim();
		local String is acceptVal: :computeAcceptKey(clientKey: clientKey);
		local String is resp: "HTTP/1.1 101 Switching Protocols\r\n"
			. "Upgrade: websocket\r\n"
			. "Connection: Upgrade\r\n"
			. 'Sec-WebSocket-Accept: ' . acceptVal . "\r\n\r\n";
		:sock:sendString(text: resp, onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err }, { :sock:close(); return false; });
		:isClient: false;
		:open: true;
		return true;
	}

	local Function of Boolean is sendFrame(Int is opcode, Array of Int is payload){
		if({ !:open }, { return false; });
		local [Byte] is frame;
		frame:push((128 | (opcode & 15)) as Byte);
		local Int is pLen: payload:length();
		local Int is maskBit: if({ :isClient }, { 128 }, { 0 });
		if({ pLen <= 125 }, {
			frame:push((maskBit | pLen) as Byte);
		}, {
			if({ pLen <= 65535 }, {
				frame:push((maskBit | 126) as Byte);
				frame:push(((pLen >> 8) & 255) as Byte);
				frame:push((pLen & 255) as Byte);
			}, {
				frame:push((maskBit | 127) as Byte);
				local Int is sh: 56;
				while({ sh >= 0 }, {
					frame:push(((pLen >> sh) & 255) as Byte);
					sh: sh - 8;
				});
			});
		});
		if({ :isClient }, {
			local Array of Int is mask: Array([55, 250, 33, 61]);
			local Int is mi: 0;
			while({ mi < 4 }, { frame:push((mask:get(index: mi, default: 0) & 255) as Byte); mi: mi + 1; });
			local Int is i: 0;
			while({ i < pLen }, {
				local Int is mb: (payload:get(index: i, default: 0) ^ mask:get(index: i % 4, default: 0)) & 255;
				frame:push(mb as Byte);
				i: i + 1;
			});
		}, {
			local Int is i2: 0;
			while({ i2 < pLen }, {
				frame:push((payload:get(index: i2, default: 0) & 255) as Byte);
				i2: i2 + 1;
			});
		});
		local Boolean is err: false;
		local Int is sent: :sock:send(data: frame, onError: local Function(SpecError of NetError is _e){ err: true; });
		return !err && sent >= 0;
	}

	## Sends a UTF-8 text WebSocket frame (opcode 0x1).
	Function of Boolean is sendText(String is text){
		local Array of Int is payload: Array();
		local Int is i: 0;
		while({ i < text:byteLength() }, {
			payload:add(item: text:byteAt(index: i, default: 0));
			i: i + 1;
		});
		return :sendFrame(opcode: 1, payload: payload);
	}

	## Receives one WebSocket text/binary frame as a String (returns '' on close/EOF).
	Function of String is receiveText(){
		if({ !:open }, { return ''; });
		local Boolean is err: false;
		local List of Byte is hdr: :sock:receive(maxBytes: 2, onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err || hdr:length() < 2 }, { :open: false; return ''; });
		local Int is b0: hdr:get(0, 0 as Byte) as Int;
		local Int is b1: hdr:get(1, 0 as Byte) as Int;
		local Int is opcode: b0 & 15;
		local Boolean is masked: (b1 & 128) != 0;
		local Int is pLen: b1 & 127;
		if({ pLen == 126 }, {
			local List of Byte is ext2: :sock:receive(maxBytes: 2, onError: local Function(SpecError of NetError is _e){ err: true; });
			if({ err || ext2:length() < 2 }, { :open: false; return ''; });
			pLen: ((ext2:get(0, 0 as Byte) as Int) << 8) | (ext2:get(1, 0 as Byte) as Int);
		}, {
			if({ pLen == 127 }, {
				local List of Byte is ext8: :sock:receive(maxBytes: 8, onError: local Function(SpecError of NetError is _e){ err: true; });
				if({ err || ext8:length() < 8 }, { :open: false; return ''; });
				pLen: 0;
				local Int is ei: 0;
				while({ ei < 8 }, {
					pLen: (pLen << 8) | (ext8:get(ei, 0 as Byte) as Int);
					ei: ei + 1;
				});
			});
		});
		local Array of Int is mask: Array([0, 0, 0, 0]);
		if({ masked }, {
			local List of Byte is mBytes: :sock:receive(maxBytes: 4, onError: local Function(SpecError of NetError is _e){ err: true; });
			if({ err || mBytes:length() < 4 }, { :open: false; return ''; });
			local Int is mi: 0;
			while({ mi < 4 }, { mask:set(index: mi, item: mBytes:get(mi, 0 as Byte) as Int); mi: mi + 1; });
		});
		local [Byte] is raw;
		while({ raw:length() < pLen }, {
			local List of Byte is chunk: :sock:receive(maxBytes: pLen - raw:length(), onError: local Function(SpecError of NetError is _e){ err: true; });
			if({ err || chunk:length() == 0 }, { :open: false; return ''; });
			raw:appendBytes(chunk);
		});
		if({ opcode == 8 }, {
			:open: false;
			return '';
		});
		if({ masked }, {
			local [Byte] is unmasked;
			local Int is i: 0;
			while({ i < pLen }, {
				local Int is u: ((raw:get(i, 0 as Byte) as Int) ^ mask:get(index: i % 4, default: 0)) & 255;
				unmasked:push(u as Byte);
				i: i + 1;
			});
			return unmasked:toString();
		});
		return raw:toString();
	}

	Function is close(){
		if({ :open }, {
			:sendFrame(opcode: 8, payload: Array());
			:open: false;
		});
		:sock:close();
	}

	Function of Boolean is isOpen(){ :open }
}
