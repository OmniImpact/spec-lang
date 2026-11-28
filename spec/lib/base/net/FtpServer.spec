#! Package base:net
#! RFC 959 FTP server supporting control commands, PASV data channel,
#! root-directory jail, and concurrent sessions over `ThreadScope`.

Class is FtpServer{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', Socket],
		['base', 'net', NetError],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as File()],
		['base', 'sys', as Dir()],
		['base', 'sys', as Process()],
		['base', 'sys', 'thread', ThreadScope]
	];

	local Socket is listener: Socket:init();
	local String is rootDir: '.';
	local String is pasvHost: '127.0.0.1';
	local String is expectedUser: 'anonymous';
	local String is expectedPass: '';
	local Boolean is requireAuth: false;
	local Boolean is running: false;
	local Int is clientTimeoutMs: 15000;

	replace Function is init(String is rootDir: '.', String is pasvHost: '127.0.0.1', Int is timeoutMs: 15000){
		:listener: Socket:init();
		:rootDir: rootDir;
		:pasvHost: pasvHost;
		:clientTimeoutMs: timeoutMs;
		:running: false;
	}

	## Configures optional username/password authentication.
	Function is setCredentials(String is username, String is password){
		:expectedUser: username;
		:expectedPass: password;
		:requireAuth: true;
	}

	## Starts listening on [host]:[port] (`port: 0` selects an ephemeral OS port).
	Function of Boolean is listen(String is host: '0.0.0.0', Int is port: 2121, Int is backlog: 64){
		local Boolean is failed: false;
		:listener: Socket:init():listen(host: host, port: port, backlog: backlog, onError: local Function(SpecError of NetError is _e){
			failed: true;
		});
		if({ failed || !:listener:isOpen() }, { return false; });
		:running: true;
		return true;
	}

	Function of Int is localPort(){
		return :listener:localPort();
	}

	Function is stop(){
		:running: false;
		:listener:close();
	}

	local Function of String is normalizeVPath(String is cwd, String is arg){
		local String is combined: if({ arg:startsWith(prefix: '/') }, { arg }, {
			if({ cwd == '/' }, { '/' . arg }, { cwd . '/' . arg })
		});
		local Array of String is parts: combined:split(delimiter: '/');
		local Array of String is stack: Array();
		local Int is i: 0;
		while({ i < parts:length() }, {
			local String is seg: parts:get(index: i, default: '');
			if({ seg == '' || seg == '.' }, {
				# skip
			}, {
				if({ seg == '..' }, {
					if({ stack:length() > 0 }, { stack:pop(default: ''); });
				}, {
					stack:add(item: seg);
				});
			});
			i: i + 1;
		});
		if({ stack:length() == 0 }, { return '/'; });
		local String is out: '';
		i: 0;
		while({ i < stack:length() }, {
			out: out . '/' . stack:get(index: i, default: '');
			i: i + 1;
		});
		return out;
	}

	local Function of String is toFsPath(String is vPath){
		if({ vPath == '/' }, { return :rootDir; });
		return :rootDir . vPath;
	}

	local Function of String is formatPasvReply(String is ip, Int is port){
		local String is csvIp: ip:replaceAll(search: '.', replacement: ',');
		local Int is p1: (port >> 8) & 255;
		local Int is p2: port & 255;
		return '227 Entering Passive Mode (' . csvIp . ',' . (p1 as String) . ',' . (p2 as String) . ")\r\n";
	}

	local Function is sendLine(Socket is sock, String is line){
		sock:sendString(text: line . "\r\n", onError: local Function(SpecError of NetError is _e){});
	}

	local Function is handleSession(Socket is ctrl){
		ctrl:setTimeout(timeoutMs: :clientTimeoutMs);
		:sendLine(sock: ctrl, line: '220 Spec FTP Server Ready');
		local String is rx: '';
		local String is cwd: '/';
		local String is pendingUser: '';
		local Boolean is authed: !:requireAuth;
		local Socket is pasvListener: Socket:init();
		local Boolean is sessionOpen: true;

		while({ sessionOpen }, {
			local Int is nl: rx:indexOf(search: "\n", default: -1);
			while({ nl < 0 && sessionOpen }, {
				local Boolean is err: false;
				local String is chunk: ctrl:receiveString(maxBytes: 4096, onError: local Function(SpecError of NetError is _e){ err: true; });
				if({ err || chunk:byteLength() == 0 }, {
					sessionOpen: false;
				}, {
					rx: rx . chunk;
					nl: rx:indexOf(search: "\n", default: -1);
				});
			});
			if({ sessionOpen && nl >= 0 }, {
				local String is rawLine: rx:substring(start: 0, end: nl):trim();
				rx: rx:substring(start: nl + 1, end: rx:length());
				local Int is sp: rawLine:indexOf(search: ' ', default: -1);
				local String is cmd: if({ sp >= 0 }, { rawLine:substring(start: 0, end: sp):toUpper() }, { rawLine:toUpper() });
				local String is arg: if({ sp >= 0 }, { rawLine:substring(start: sp + 1, end: rawLine:length()):trim() }, { '' });

				if({ cmd == 'QUIT' }, {
					:sendLine(sock: ctrl, line: '221 Goodbye');
					sessionOpen: false;
				}, {
				if({ cmd == 'USER' }, {
					pendingUser: arg;
					if({ !:requireAuth }, {
						authed: true;
						:sendLine(sock: ctrl, line: '230 Logged in');
					}, {
						:sendLine(sock: ctrl, line: '331 Password required');
					});
				}, {
				if({ cmd == 'PASS' }, {
					if({ !:requireAuth || (pendingUser == :expectedUser && arg == :expectedPass) }, {
						authed: true;
						:sendLine(sock: ctrl, line: '230 Logged in');
					}, {
						:sendLine(sock: ctrl, line: '530 Login incorrect');
					});
				}, {
				if({ cmd == 'SYST' }, {
					:sendLine(sock: ctrl, line: '215 UNIX Type: L8');
				}, {
				if({ cmd == 'FEAT' }, {
					:sendLine(sock: ctrl, line: '211 End');
				}, {
				if({ cmd == 'NOOP' }, {
					:sendLine(sock: ctrl, line: '200 OK');
				}, {
				if({ cmd == 'TYPE' }, {
					:sendLine(sock: ctrl, line: '200 Type set');
				}, {
				if({ !authed }, {
					:sendLine(sock: ctrl, line: '530 Not logged in');
				}, {
				if({ cmd == 'PWD' }, {
					:sendLine(sock: ctrl, line: '257 "' . cwd . '" is current directory');
				}, {
				if({ cmd == 'CWD' }, {
					local String is targetV: :normalizeVPath(cwd: cwd, arg: arg);
					local String is targetFs: :toFsPath(vPath: targetV);
					if({ Dir:isDir(path: targetFs) }, {
						cwd: targetV;
						:sendLine(sock: ctrl, line: '250 Directory changed');
					}, {
						:sendLine(sock: ctrl, line: '550 Directory not found');
					});
				}, {
				if({ cmd == 'CDUP' }, {
					cwd: :normalizeVPath(cwd: cwd, arg: '..');
					:sendLine(sock: ctrl, line: '250 Directory changed');
				}, {
				if({ cmd == 'PASV' }, {
					pasvListener:close();
					local Boolean is pErr: false;
					pasvListener: Socket:init():listen(host: :pasvHost, port: 0, backlog: 4, onError: local Function(SpecError of NetError is _e){ pErr: true; });
					if({ pErr || !pasvListener:isOpen() }, {
						:sendLine(sock: ctrl, line: '425 Cannot open passive connection');
					}, {
						local Int is pPort: pasvListener:localPort();
						ctrl:sendString(text: :formatPasvReply(ip: :pasvHost, port: pPort), onError: local Function(SpecError of NetError is _e){});
					});
				}, {
				if({ cmd == 'LIST' }, {
					if({ !pasvListener:isOpen() }, {
						:sendLine(sock: ctrl, line: '425 Use PASV first');
					}, {
						:sendLine(sock: ctrl, line: '150 Opening data connection');
						local Socket is dataSock: pasvListener:accept(onError: local Function(SpecError of NetError is _e){});
						local String is listV: if({ arg == '' }, { cwd }, { :normalizeVPath(cwd: cwd, arg: arg) });
						local Array of String is entries: Dir:dirList(path: :toFsPath(vPath: listV));
						local String is listing: '';
						local Int is ei: 0;
						while({ ei < entries:length() }, {
							listing: listing . entries:get(index: ei, default: '') . "\r\n";
							ei: ei + 1;
						});
						if({ dataSock:isOpen() }, {
							dataSock:sendString(text: listing, onError: local Function(SpecError of NetError is _e){});
							dataSock:close();
						});
						pasvListener:close();
						:sendLine(sock: ctrl, line: '226 Transfer complete');
					});
				}, {
				if({ cmd == 'RETR' }, {
					local String is fV: :normalizeVPath(cwd: cwd, arg: arg);
					local String is fFs: :toFsPath(vPath: fV);
					if({ !pasvListener:isOpen() }, {
						:sendLine(sock: ctrl, line: '425 Use PASV first');
					}, {
						if({ !File:fileExists(path: fFs) }, {
							:sendLine(sock: ctrl, line: '550 File not found');
						}, {
							:sendLine(sock: ctrl, line: '150 Opening data connection');
							local Socket is dataSock: pasvListener:accept(onError: local Function(SpecError of NetError is _e){});
							local String is content: File:fileRead(path: fFs, onSuccess: local Function(String is _s){}, onError: local Function(SpecError of FileError is _e){}, default: '');
							if({ dataSock:isOpen() }, {
								dataSock:sendString(text: content, onError: local Function(SpecError of NetError is _e){});
								dataSock:close();
							});
							pasvListener:close();
							:sendLine(sock: ctrl, line: '226 Transfer complete');
						});
					});
				}, {
				if({ cmd == 'STOR' }, {
					local String is fV: :normalizeVPath(cwd: cwd, arg: arg);
					local String is fFs: :toFsPath(vPath: fV);
					if({ !pasvListener:isOpen() }, {
						:sendLine(sock: ctrl, line: '425 Use PASV first');
					}, {
						:sendLine(sock: ctrl, line: '150 Ready to receive');
						local Socket is dataSock: pasvListener:accept(onError: local Function(SpecError of NetError is _e){});
						local String is payload: '';
						if({ dataSock:isOpen() }, {
							dataSock:setTimeout(timeoutMs: :clientTimeoutMs);
							local Boolean is readingData: true;
							while({ readingData }, {
								local Boolean is dErr: false;
								local String is c: dataSock:receiveString(maxBytes: 8192, onError: local Function(SpecError of NetError is _e){ dErr: true; });
								if({ dErr || c:byteLength() == 0 }, {
									readingData: false;
								}, {
									payload: payload . c;
								});
							});
							dataSock:close();
						});
						pasvListener:close();
						local Boolean is wrote: File:fileWrite(path: fFs, content: payload, onSuccess: local Function(Int is _n){}, onError: local Function(SpecError of FileError is _e){});
						if({ wrote }, {
							:sendLine(sock: ctrl, line: '226 Transfer complete');
						}, {
							:sendLine(sock: ctrl, line: '550 Write failed');
						});
					});
				}, {
				if({ cmd == 'DELE' }, {
					local String is fV: :normalizeVPath(cwd: cwd, arg: arg);
					local String is fFs: :toFsPath(vPath: fV);
					local Boolean is ok: File:fileRemove(path: fFs, onError: local Function(SpecError of FileError is _e){});
					if({ ok }, { :sendLine(sock: ctrl, line: '250 File deleted'); }, { :sendLine(sock: ctrl, line: '550 Delete failed'); });
				}, {
				if({ cmd == 'SIZE' }, {
					local String is fV: :normalizeVPath(cwd: cwd, arg: arg);
					local String is fFs: :toFsPath(vPath: fV);
					if({ File:fileExists(path: fFs) }, {
						:sendLine(sock: ctrl, line: '213 ' . (Dir:fileSize(path: fFs) as String));
					}, {
						:sendLine(sock: ctrl, line: '550 File not found');
					});
				}, {
				if({ cmd == 'MKD' }, {
					local String is dV: :normalizeVPath(cwd: cwd, arg: arg);
					local Boolean is ok: Dir:makeDirAll(path: :toFsPath(vPath: dV));
					if({ ok }, { :sendLine(sock: ctrl, line: '257 "' . dV . '" created'); }, { :sendLine(sock: ctrl, line: '550 MKD failed'); });
				}, {
				if({ cmd == 'RMD' }, {
					local String is dV: :normalizeVPath(cwd: cwd, arg: arg);
					local Boolean is ok2: Dir:removeDir(path: :toFsPath(vPath: dV));
					if({ ok2 }, { :sendLine(sock: ctrl, line: '250 Directory removed'); }, { :sendLine(sock: ctrl, line: '550 RMD failed'); });
				}, {
					:sendLine(sock: ctrl, line: '502 Command not implemented');
				}); }); }); }); }); }); }); }); }); }); }); }); }); }); }); }); }); }); });
			});
		});
		pasvListener:close();
		ctrl:close();
	}

	## Accepts and handles one FTP client session synchronously.
	Function of Boolean is serveOne(){
		if({ !:running }, { return false; });
		local Boolean is err: false;
		local Socket is client: :listener:accept(onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err || !client:isOpen() }, { return false; });
		:handleSession(ctrl: client);
		return true;
	}

	## Runs a concurrent FTP accept loop inside [scope] until `stop()` is called.
	Function is serve(ThreadScope is scope){
		while({ :running }, {
			if({ :listener:poll(mode: 1, timeoutMs: 100) }, {
				local Boolean is err: false;
				local Socket is client: :listener:accept(onError: local Function(SpecError of NetError is _e){ err: true; });
				if({ !err && client:isOpen() }, {
					scope:spawn(task: local Function(){
						:handleSession(ctrl: client);
					});
				});
			});
		});
	}
}
