#! specunit: suite

Class of SpecUnitTest is TestWebSocketAndFtpClient{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'core', SpecError],
		['base', 'struct', Array],
		['base', 'math', 'crypto', as Sha1()],
		['base', 'net', [Socket, NetError, WebSocket, FtpServer, FtpClient]],
		['base', 'sys', as Dir()],
		['base', 'sys', as Process()],
		['base', 'sys', as Uri()],
		['base', 'sys', 'thread', [ThreadScope, Task]]
	];

	Function is testSha1AndWebSocketLoopback(){
		# RFC 3174 SHA-1("abc") starts with a9 99 3e 36
		local Array of Int is h: Sha1:digestString(text: 'abc');
		Assert:areEqualInt(20, h:length());
		Assert:areEqualInt(169, h:get(index: 0, default: 0));
		Assert:areEqualInt(153, h:get(index: 1, default: 0));
		Assert:areEqualInt(62, h:get(index: 2, default: 0));
		Assert:areEqualInt(54, h:get(index: 3, default: 0));

		# RFC 6455 Sec-WebSocket-Accept exact test vector
		local WebSocket is wsHelper: WebSocket:init();
		Assert:areEqualString('s3pPLMBiTxaQ9kYGzzhZRbK+xOo=', wsHelper:computeAcceptKey(clientKey: 'dGhlIHNhbXBsZSBub25jZQ=='));

		local Socket is listener: Socket:init():listen(host: '127.0.0.1', port: 0);
		local Int is port: listener:localPort();
		Assert:isTrue(port > 0);

		local String is srvGot: '';
		local String is cliGot: '';
		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _e){ return false; },
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					local Socket is cSock: listener:accept();
					local WebSocket is srvWs: WebSocket:init();
					if({ srvWs:acceptHandshake(clientSocket: cSock, timeoutMs: 5000) }, {
						srvGot: srvWs:receiveText();
						srvWs:sendText(text: 'ws-pong');
					});
					srvWs:close();
				});
				scope:spawn(task: local Function(){
					local WebSocket is cliWs: WebSocket:init();
					if({ cliWs:connect(host: '127.0.0.1', port: port, path: '/chat', timeoutMs: 5000) }, {
						cliWs:sendText(text: 'ws-ping');
						cliGot: cliWs:receiveText();
					});
					cliWs:close();
				});
			}
		);
		listener:close();

		Assert:areEqualString('ws-ping', srvGot);
		Assert:areEqualString('ws-pong', cliGot);
	}

	Function is testFtpClientServerRoundTrip(){
		local String is root: Uri:systemTempDir() . '/spec_ftp_cli_test_' . (Process:getPid() as String);
		Assert:isTrue(Dir:makeDirAll(path: root));

		local FtpServer is srv: FtpServer:init(rootDir: root, pasvHost: '127.0.0.1', timeoutMs: 5000);
		srv:setCredentials(username: 'bob', password: 'pw');
		Assert:isTrue(srv:listen(host: '127.0.0.1', port: 0));
		local Int is port: srv:localPort();

		local Boolean is loggedIn: false;
		local Boolean is uploaded: false;
		local String is listing: '';
		local String is downloaded: '';
		local Boolean is deleted: false;

		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _e){ return false; },
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					srv:serveOne();
				});
				scope:spawn(task: local Function(){
					local FtpClient is cli: FtpClient:init(timeoutMs: 5000);
					if({ cli:connect(host: '127.0.0.1', port: port) }, {
						loggedIn: cli:login(username: 'bob', password: 'pw');
						uploaded: cli:upload(remotePath: 'doc.txt', content: 'hello-ftp-client');
						listing: cli:list();
						downloaded: cli:download(remotePath: 'doc.txt');
						deleted: cli:delete(path: 'doc.txt');
						cli:quit();
					});
				});
			}
		);
		srv:stop();
		Dir:removeDir(path: root);

		Assert:isTrue(loggedIn);
		Assert:isTrue(uploaded);
		Assert:isTrue(listing:contains(needle: 'doc.txt'));
		Assert:areEqualString('hello-ftp-client', downloaded);
		Assert:isTrue(deleted);
	}
}
