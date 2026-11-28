#! specunit: suite

Class of SpecUnitTest is TestTlsServer{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'core', SpecError],
		['base', 'struct', Array],
		['base', 'math', 'crypto', as Sha512()],
		['base', 'math', 'crypto', as Ed25519()],
		['base', 'math', 'crypto', as Pem()],
		['base', 'net', 'tls', [TlsClient, TlsServer, TlsServerSession, TlsError]],
		['base', 'sys', 'thread', [ThreadScope, Task]]
	];

	Function is testSha512Ed25519AndPem(){
		# RFC 6234 SHA-512("abc") starts with ddaf35a1 93617aba ...
		local Array of Int is h: Sha512:hash(msg: Array([97, 98, 99]));
		Assert:areEqualInt(64, h:length());
		Assert:areEqualInt(221, h:get(index: 0, default: 0));
		Assert:areEqualInt(175, h:get(index: 1, default: 0));
		Assert:areEqualInt(53, h:get(index: 2, default: 0));
		Assert:areEqualInt(161, h:get(index: 3, default: 0));

		# Ed25519 sign + verify + tamper rejection
		local Array of Int is seed: Array([
			157, 97, 177, 157, 239, 253, 90, 96, 186, 132, 74, 244, 146, 236, 44, 196,
			68, 73, 197, 105, 123, 50, 105, 25, 112, 59, 172, 3, 28, 174, 127, 96
		]);
		local Array of Int is pub: Ed25519:publicKey(seed: seed);
		Assert:areEqualInt(32, pub:length());
		# RFC 8032 test vector 1 public key starts with d75a9801
		Assert:areEqualInt(215, pub:get(index: 0, default: 0));
		Assert:areEqualInt(90, pub:get(index: 1, default: 0));
		Assert:areEqualInt(152, pub:get(index: 2, default: 0));
		Assert:areEqualInt(1, pub:get(index: 3, default: 0));

		local Array of Int is msg: Array([115, 112, 101, 99]);
		local Array of Int is sig: Ed25519:sign(seed: seed, msg: msg);
		Assert:areEqualInt(64, sig:length());
		Assert:isTrue(Ed25519:verify(pubKey: pub, msg: msg, sig: sig));

		local Array of Int is badMsg: Array([115, 112, 101, 100]);
		Assert:isFalse(Ed25519:verify(pubKey: pub, msg: badMsg, sig: sig));

		# PEM decode
		local String is pem: "-----BEGIN TEST-----\nU3BlYw==\n-----END TEST-----\n";
		local Array of Array of Int is blocks: Pem:decodeBlocks(pemText: pem, label: 'TEST');
		Assert:areEqualInt(1, blocks:length());
		Assert:areEqualInt(4, blocks:get(index: 0):length());
		Assert:areEqualInt(83, blocks:get(index: 0):get(index: 0, default: 0));
	}

	Function is testTls13ServerClientLoopbackHandshake(){
		local Array of Int is seed: Array([
			1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
			17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32
		]);
		local Array of Array of Int is certs: Array([Array([48, 3, 2, 1, 1])]);

		local TlsServer is srv: TlsServer:init();
		srv:setCredentials(certChain: certs, ed25519Seed: seed);
		Assert:isTrue(srv:listen(host: '127.0.0.1', port: 0));
		local Int is port: srv:localPort();
		Assert:isTrue(port > 0);

		local String is srvGot: '';
		local String is cliGot: '';
		local String is sniSeen: '';
		local Boolean is cliOk: false;

		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _e){ return false; },
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					local TlsServerSession is sess: srv:accept(timeoutMs: 5000);
					if({ sess:isConnected() }, {
						sniSeen: sess:clientSni();
						srvGot: sess:recvString();
						sess:sendString(text: 'hello-from-tls-server');
					});
					sess:close();
				});
				scope:spawn(task: local Function(){
					local TlsClient is cli: TlsClient:init();
					cliOk: cli:connect(host: '127.0.0.1', port: port, timeoutMs: 5000, verifyCert: false);
					if({ cliOk }, {
						cli:sendString(text: 'hello-from-tls-client');
						cliGot: cli:recvAllString();
					});
					cli:close();
				});
			}
		);
		srv:close();

		Assert:isTrue(cliOk);
		Assert:areEqualString('127.0.0.1', sniSeen);
		Assert:areEqualString('hello-from-tls-client', srvGot);
		Assert:areEqualString('hello-from-tls-server', cliGot);
	}
}
