#! PCM sine-wave synthesizer and MIDI pitch helper for RandomTune.

## Converts MIDI note numbers to frequencies and synthesizes 16-bit stereo PCM sine waves.
Class is Synth{

	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'math', as Math()],
		['base', 'struct', List]
	];

	## Converts a [midi] note number (A4 = 69 = 440 Hz) to frequency in Hz.
	Function of Float is midiToFreq(Int is midi){
		return 440.0 * Math:pow(base: 2.0, exp: ((midi - 69) as Float) / 12.0);
	}

	## Synthesizes a 16-bit signed little-endian stereo PCM sine wave at [freqHz] for [durationMs] at [sampleRate] Hz.
	Function of List of Byte is synthesizeSine(Float is freqHz, Int is durationMs, Int is sampleRate){
		local List of Byte is buf;
		local Int is totalSamples: (sampleRate * durationMs) / 1000;
		local Int is fadeSamples: (sampleRate * 15) / 1000;
		local Float is twoPi: 6.283185307179586;
		local Float is amplitude: 12000.0;

		while([Int is i: 0], { i < totalSamples }, {
			local Float is env: 1.0;
			if({ i < fadeSamples && fadeSamples > 0 }, {
				env: (i as Float) / (fadeSamples as Float);
			});
			if({ i > (totalSamples - fadeSamples) && fadeSamples > 0 }, {
				env: ((totalSamples - i) as Float) / (fadeSamples as Float);
			});
			local Float is t: (i as Float) / (sampleRate as Float);
			local Float is sampleVal: Math:sin(x: twoPi * freqHz * t) * amplitude * env;
			local Int is s: Math:toInt(x: Math:round(x: sampleVal));
			if({ s < 0 }, {
				s: s + 65536;
			});
			local Int is lo: s & 255;
			local Int is hi: (s >> 8) & 255;

			buf:push(lo);
			buf:push(hi);
			buf:push(lo);
			buf:push(hi);
			i: i + 1;
		});
		return buf;
	}

}
