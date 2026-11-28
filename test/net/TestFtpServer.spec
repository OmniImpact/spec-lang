#! specunit: suite

Class of SpecUnitTest is TestFtpServer{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'core', SpecError],
		['base', 'struct', Array],
		['base', 'net', [Socket, NetError, FtpServer]],
		['base', 'sys', as File()],
		['base', 'sys', as Dir()],
		['base', 'sys', as Process()],
		['base', 'sys', as Uri()],
		['base', 'sys', 'thread', [ThreadScope, Task]]
	];

	local Function of Int is parsePasvPort(String is reply){
		local Int is lp: reply:indexOf(search: '(', default: -1);
		local Int is rp: reply:indexOf(search: ')', default: -1);
		if({ lp < 0 || rp <= lp }, { return -1; });
		local String is inside: reply:substring(start: lp + 1, end: rp);
		local Array of String is parts: inside:split(delimiter: ',');
		if({ parts:length() < 6 }, { return -1; });
		local Int is p1: parts:get(index: 4, default: '0'):parseInt(default: 0);
		local Int is p2: parts:get(index: 5, default: '0'):parseInt(default: 0);
		return p1 * 256 + p2;
	}

	Function is testFtpAuthPasvStorRetrListDeleAndJail(){
		local String is root: Uri:systemTempDir() . '/spec_ftp_test_' . (Process:getPid() as String);
		Process:execute(command: 'mkdir', args: Array(['-p', root]));

		local FtpServer is srv: FtpServer:init(rootDir: root, pasvHost: '127.0.0.1', timeoutMs: 5000);
		srv:setCredentials(username: 'alice', password: 'secret');
		Assert:isTrue(srv:listen(host: '127.0.0.1', port: 0));
		local Int is port: srv:localPort();
		Assert:isTrue(port > 0);

		local String is downloaded: '';
		local String is listOut: '';
		local String is pwdAfterJail: '';
		local Boolean is badAuthRejected: false;
		local Boolean is sizeOk: false;
		local Boolean is deleOk: false;

		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _e){ return false; },
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					srv:serveOne();
				});
				scope:spawn(task: local Function(){
					local Socket is c: Socket:init():connect(host: '127.0.0.1', port: port, timeoutMs: 5000);
					c:setTimeout(timeoutMs: 5000);
					local String is greet: c:receiveString(maxBytes: 1024);
					Assert:isTrue(greet:startsWith(prefix: '220'));

					# Wrong password -> 530
					c:sendString(text: "USER alice\r\n");
					c:receiveString(maxBytes: 1024);
					c:sendString(text: "PASS wrong\r\n");
					local String is rBad: c:receiveString(maxBytes: 1024);
					badAuthRejected: rBad:startsWith(prefix: '530');

					# Valid auth -> 230
					c:sendString(text: "PASS secret\r\n");
					local String is rOk: c:receiveString(maxBytes: 1024);
					Assert:isTrue(rOk:startsWith(prefix: '230'));

					# Root jail check: CWD ../../.. must stay at /
					c:sendString(text: "CWD ../../../..\r\n");
					c:receiveString(maxBytes: 1024);
					c:sendString(text: "PWD\r\n");
					pwdAfterJail: c:receiveString(maxBytes: 1024);

					# PASV + STOR upload
					c:sendString(text: "PASV\r\n");
					local String is pasv1: c:receiveString(maxBytes: 1024);
					local Int is dp1: :parsePasvPort(reply: pasv1);
					c:sendString(text: "STOR hello.txt\r\n");
					c:receiveString(maxBytes: 1024);
					local Socket is d1: Socket:init():connect(host: '127.0.0.1', port: dp1, timeoutMs: 5000);
					d1:sendString(text: 'ftp-payload-123');
					d1:close();
					c:receiveString(maxBytes: 1024);

					# SIZE
					c:sendString(text: "SIZE hello.txt\r\n");
					local String is rSize: c:receiveString(maxBytes: 1024);
					sizeOk: rSize:contains(needle: '213 15');

					# PASV + LIST
					c:sendString(text: "PASV\r\n");
					local Int is dp2: :parsePasvPort(reply: c:receiveString(maxBytes: 1024));
					c:sendString(text: "LIST\r\n");
					c:receiveString(maxBytes: 1024);
					local Socket is d2: Socket:init():connect(host: '127.0.0.1', port: dp2, timeoutMs: 5000);
					listOut: d2:receiveString(maxBytes: 4096);
					d2:close();
					c:receiveString(maxBytes: 1024);

					# PASV + RETR
					c:sendString(text: "PASV\r\n");
					local Int is dp3: :parsePasvPort(reply: c:receiveString(maxBytes: 1024));
					c:sendString(text: "RETR hello.txt\r\n");
					c:receiveString(maxBytes: 1024);
					local Socket is d3: Socket:init():connect(host: '127.0.0.1', port: dp3, timeoutMs: 5000);
					downloaded: d3:receiveString(maxBytes: 4096);
					d3:close();
					c:receiveString(maxBytes: 1024);

					# DELE + QUIT
					c:sendString(text: "DELE hello.txt\r\n");
					deleOk: c:receiveString(maxBytes: 1024):startsWith(prefix: '250');
					c:sendString(text: "QUIT\r\n");
					c:receiveString(maxBytes: 1024);
					c:close();
				});
			}
		);
		srv:stop();
		Process:execute(command: 'rmdir', args: Array([root]));

		Assert:isTrue(badAuthRejected);
		Assert:isTrue(pwdAfterJail:contains(needle: '257 "/"'));
		Assert:isTrue(sizeOk);
		Assert:isTrue(listOut:contains(needle: 'hello.txt'));
		Assert:areEqualString('ftp-payload-123', downloaded);
		Assert:isTrue(deleOk);
	}
}
