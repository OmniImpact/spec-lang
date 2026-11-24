#! specunit: suite

Class of SpecUnitTest is TestRandomTune{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		['base', 'math', as Math()],
		['base', 'struct', List],
		[Synth]
	];

	Function is testMidiToFreq(){
		local Synth is s: Synth();
		local Int is a4: Math:toInt(value: Math:round(value: s:midiToFreq(midi: 69)));
		local Int is a5: Math:toInt(value: Math:round(value: s:midiToFreq(midi: 81)));
		Assert:areEqualInt(440, a4);
		Assert:areEqualInt(880, a5);
	}

	Function is testSynthesizeSineBufferLength(){
		local Synth is s: Synth();
		local List of Byte is pcm: s:synthesizeSine(freqHz: 440.0, durationMs: 100, sampleRate: 8000);
		# 8000 * 0.1s = 800 stereo 16-bit frames * 4 bytes/frame = 3200 bytes
		Assert:areEqualInt(3200, pcm:length());
	}

}
