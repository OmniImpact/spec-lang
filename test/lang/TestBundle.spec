#! specunit: suite

Class of SpecUnitTest is TestBundle{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', [Bundle, as Dir()]]
	];

	Function is testExePathNonEmpty(){
		Assert:isTrue(exePath() != '');
	}

	Function is testPackAndUnpackRoundTrip(){
		local Bundle is packer: Bundle(autoLoad: false);
		local Array of String is dests: Array(['locations.json', 'assets/info.txt']);
		local Array of String is payloads: Array(['{"states":[]}', 'hello bundle']);
		local String is blob: packer:pack(destPaths: dests, payloads: payloads);

		local String is fakeExe: 'ELF_HEADER_DUMMY_BYTES' . blob;
		local Bundle is reader: Bundle(autoLoad: false);
		Assert:isTrue(reader:loadFromBytes(raw: fakeExe));
		Assert:isTrue(reader:isBundled());
		Assert:isTrue(reader:has(path: 'locations.json'));
		Assert:isTrue(reader:has(path: './assets/info.txt'));
		Assert:isFalse(reader:has(path: 'missing.txt'));
		Assert:areEqualString('{"states":[]}', reader:readText(path: 'locations.json'));
		Assert:areEqualString('hello bundle', reader:readText(path: 'assets/info.txt'));
		Assert:areEqualString('fallback', reader:readText(path: 'missing.txt', default: 'fallback'));
		Assert:areEqualInt(1, reader:list(prefix: 'assets/'):length());
	}
}
