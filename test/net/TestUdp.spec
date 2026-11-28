#! specunit: suite

Class of SpecUnitTest is TestUdp{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'core', SpecError],
		['base', 'net', [Socket, UdpSocket, UdpPacket, NetError]]
	];

	Function is testUdpLoopbackAndLocalPort(){
		local UdpSocket is srv: UdpSocket:init():bind(host: '127.0.0.1', port: 0);
		Assert:isTrue(srv:isOpen());
		local Int is srvPort: srv:localPort();
		Assert:isTrue(srvPort > 0);
		srv:setTimeout(timeoutMs: 1000);

		local UdpSocket is cli: UdpSocket:init():bind(host: '127.0.0.1', port: 0);
		local Int is cliPort: cli:localPort();
		Assert:isTrue(cliPort > 0);
		cli:setTimeout(timeoutMs: 1000);

		local Int is sent: cli:sendStringTo(host: '127.0.0.1', port: srvPort, text: 'hello-udp');
		Assert:areEqualInt(9, sent);

		Assert:isTrue(srv:poll(mode: 1, timeoutMs: 500));
		local UdpPacket is pkt: srv:receiveFrom(maxBytes: 256);
		Assert:areEqualInt(9, pkt:length);
		Assert:areEqualString('hello-udp', pkt:text());
		Assert:areEqualString('127.0.0.1', pkt:host);
		Assert:areEqualInt(cliPort, pkt:port);

		# Echo back to peer
		local Int is sent2: srv:sendStringTo(host: pkt:host, port: pkt:port, text: 'pong');
		Assert:areEqualInt(4, sent2);
		local UdpPacket is reply: cli:receiveFrom(maxBytes: 256);
		Assert:areEqualString('pong', reply:text());
		Assert:areEqualInt(srvPort, reply:port);

		cli:close();
		srv:close();
		Assert:isFalse(srv:isOpen());
	}

	Function is testTcpEphemeralListenLocalPort(){
		local Socket is listener: Socket:init():listen(host: '127.0.0.1', port: 0);
		Assert:isTrue(listener:isOpen());
		local Int is p: listener:localPort();
		Assert:isTrue(p > 0);
		listener:close();
		Assert:areEqualInt(-1, listener:localPort());
	}
}
