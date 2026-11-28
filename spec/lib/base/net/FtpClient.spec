#! Package base:net
#! RFC 959 FTP client supporting authentication, PASV transfers, LIST, RETR, STOR, DELE, PWD, CWD.

Class is FtpClient{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', Socket],
		['base', 'net', NetError],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Socket is ctrl: Socket:init();
	local String is host: '';
	local Int is timeoutMs: 10000;
	local String is lastReply: '';

	replace Function is init(Int is timeoutMs: 10000){
		:ctrl: Socket:init();
		:timeoutMs: timeoutMs;
	}

	local Function of String is readReply(){
		local Boolean is err: false;
		local String is r: :ctrl:receiveString(maxBytes: 4096, onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err }, { :lastReply: ''; return ''; });
		:lastReply: r:trim();
		return :lastReply;
	}

	local Function of String is sendCmd(String is cmd){
		local Boolean is err: false;
		:ctrl:sendString(text: cmd . "\r\n", onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err }, { return ''; });
		return :readReply();
	}

	local Function of Int is openPasvPort(){
		local String is r: :sendCmd(cmd: 'PASV');
		local Int is lp: r:indexOf(search: '(', default: -1);
		local Int is rp: r:indexOf(search: ')', default: -1);
		if({ lp < 0 || rp <= lp }, { return -1; });
		local Array of String is parts: r:substring(start: lp + 1, end: rp):split(delimiter: ',');
		if({ parts:length() < 6 }, { return -1; });
		return parts:get(index: 4, default: '0'):parseInt(default: 0) * 256 + parts:get(index: 5, default: '0'):parseInt(default: 0);
	}

	Function of Boolean is connect(String is host, Int is port: 21){
		:host: host;
		local Boolean is err: false;
		:ctrl: Socket:init():connect(host: host, port: port, timeoutMs: :timeoutMs, onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err || !:ctrl:isOpen() }, { return false; });
		:ctrl:setTimeout(timeoutMs: :timeoutMs);
		local String is greet: :readReply();
		return greet:startsWith(prefix: '220');
	}

	Function of Boolean is login(String is username, String is password: ''){
		local String is r1: :sendCmd(cmd: 'USER ' . username);
		if({ r1:startsWith(prefix: '230') }, { return true; });
		if({ !r1:startsWith(prefix: '331') }, { return false; });
		local String is r2: :sendCmd(cmd: 'PASS ' . password);
		return r2:startsWith(prefix: '230');
	}

	Function of String is pwd(){
		return :sendCmd(cmd: 'PWD');
	}

	Function of Boolean is cwd(String is dir){
		return :sendCmd(cmd: 'CWD ' . dir):startsWith(prefix: '250');
	}

	Function of Boolean is delete(String is path){
		return :sendCmd(cmd: 'DELE ' . path):startsWith(prefix: '250');
	}

	Function of Boolean is upload(String is remotePath, String is content){
		local Int is dp: :openPasvPort();
		if({ dp <= 0 }, { return false; });
		local String is r1: :sendCmd(cmd: 'STOR ' . remotePath);
		if({ !r1:startsWith(prefix: '150') }, { return false; });
		local Socket is data: Socket:init():connect(host: :host, port: dp, timeoutMs: :timeoutMs, onError: local Function(SpecError of NetError is _e){});
		if({ !data:isOpen() }, { return false; });
		data:sendString(text: content, onError: local Function(SpecError of NetError is _e){});
		data:close();
		local String is r2: :readReply();
		return r2:startsWith(prefix: '226');
	}

	Function of String is download(String is remotePath){
		local Int is dp: :openPasvPort();
		if({ dp <= 0 }, { return ''; });
		local String is r1: :sendCmd(cmd: 'RETR ' . remotePath);
		if({ !r1:startsWith(prefix: '150') }, { return ''; });
		local Socket is data: Socket:init():connect(host: :host, port: dp, timeoutMs: :timeoutMs, onError: local Function(SpecError of NetError is _e){});
		local String is out: '';
		if({ data:isOpen() }, {
			data:setTimeout(timeoutMs: :timeoutMs);
			local Boolean is reading: true;
			while({ reading }, {
				local Boolean is dErr: false;
				local String is c: data:receiveString(maxBytes: 8192, onError: local Function(SpecError of NetError is _e){ dErr: true; });
				if({ dErr || c:byteLength() == 0 }, { reading: false; }, { out: out . c; });
			});
			data:close();
		});
		:readReply();
		return out;
	}

	Function of String is list(String is path: ''){
		local Int is dp: :openPasvPort();
		if({ dp <= 0 }, { return ''; });
		local String is cmd: if({ path == '' }, { 'LIST' }, { 'LIST ' . path });
		local String is r1: :sendCmd(cmd: cmd);
		if({ !r1:startsWith(prefix: '150') }, { return ''; });
		local Socket is data: Socket:init():connect(host: :host, port: dp, timeoutMs: :timeoutMs, onError: local Function(SpecError of NetError is _e){});
		local String is out: '';
		if({ data:isOpen() }, {
			data:setTimeout(timeoutMs: :timeoutMs);
			local Boolean is reading: true;
			while({ reading }, {
				local Boolean is dErr: false;
				local String is c: data:receiveString(maxBytes: 8192, onError: local Function(SpecError of NetError is _e){ dErr: true; });
				if({ dErr || c:byteLength() == 0 }, { reading: false; }, { out: out . c; });
			});
			data:close();
		});
		:readReply();
		return out;
	}

	Function is quit(){
		if({ :ctrl:isOpen() }, {
			:sendCmd(cmd: 'QUIT');
			:ctrl:close();
		});
	}

	Function of String is getLastReply(){ :lastReply }
}
