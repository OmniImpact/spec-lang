#! Package base:net:tls
#! TLS 1.3 TCP server listener accepting [TlsServerSession] connections.

Class is TlsServer{
	replace [String] is namespace: ['base', 'net', 'tls'];

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', Socket],
		['base', 'net', NetError],
		['base', 'net', 'tls', TlsServerSession],
		['base', 'math', 'crypto', as Pem()],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	local Socket is listener: Socket:init();
	local Array of Array of Int is certChain: Array();
	local Array of Int is ed25519Seed: Array();
	local Boolean is running: false;

	replace Function is init(){
		:listener: Socket:init();
		:certChain: Array();
		:ed25519Seed: Array();
		:running: false;
	}

	## Configures the server certificate chain (DER bytes) and 32-byte Ed25519 private seed.
	Function is setCredentials(Array of Array of Int is certChain, Array of Int is ed25519Seed){
		:certChain: certChain;
		:ed25519Seed: ed25519Seed;
	}

	## Configures credentials from PEM-encoded certificate chain and PKCS#8 Ed25519 private key.
	Function of Boolean is loadPemCredentials(String is certPem, String is keyPem){
		local Array of Array of Int is certs: Pem:decodeBlocks(pemText: certPem, label: 'CERTIFICATE');
		local Array of Array of Int is keys: Pem:decodeBlocks(pemText: keyPem, label: 'PRIVATE KEY');
		if({ certs:length() == 0 || keys:length() == 0 }, { return false; });
		local Array of Int is seed: Pem:extractEd25519Seed(der: keys:get(index: 0));
		if({ seed:length() != 32 }, { return false; });
		:certChain: certs;
		:ed25519Seed: seed;
		return true;
	}

	## Binds and listens on [host]:[port] (`port: 0` selects an ephemeral OS port).
	Function of Boolean is listen(String is host: '0.0.0.0', Int is port: 443, Int is backlog: 128){
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

	Function of Boolean is poll(Int is timeoutMs: 0){
		return :listener:poll(mode: 1, timeoutMs: timeoutMs);
	}

	## Accepts one TCP client and performs the TLS 1.3 server handshake.
	Function of TlsServerSession is accept(Int is timeoutMs: 15000){
		local TlsServerSession is sess: TlsServerSession:init();
		if({ !:running }, { return sess; });
		local Boolean is err: false;
		local Socket is client: :listener:accept(onError: local Function(SpecError of NetError is _e){ err: true; });
		if({ err || !client:isOpen() }, { return sess; });
		sess:acceptHandshake(clientSocket: client, certChain: :certChain, ed25519Seed: :ed25519Seed, timeoutMs: timeoutMs);
		return sess;
	}

	Function is close(){
		:running: false;
		:listener:close();
	}

	Function of Boolean is isOpen(){
		return :running && :listener:isOpen();
	}
}
