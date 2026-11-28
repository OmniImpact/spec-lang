#! Package base:net
#! Received UDP datagram carrying payload bytes and sender address (`host`, `port`).

Class is UdpPacket{
	replace [String] is namespace: ['base', 'net'];

	replace [[String]] is using: [
		['base', 'struct', List]
	];

	List of Byte is data;
	String is host: '';
	Int is port: 0;
	Int is length: 0;

	replace Function is init(List of Byte is data, String is host: '', Int is port: 0, Int is length: 0){
		:data: data;
		:host: host;
		:port: port;
		:length: length;
	}

	Function of String is text(){
		return :data:toString();
	}
}
