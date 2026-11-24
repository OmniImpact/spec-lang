#! Package theosynth:model
#! Multi-waveform PCM synthesizer (Sine, Square, Sawtooth) and safe audio output wrapper.

Class is SynthEngine{
	replace [String] is namespace: ['theosynth', 'model'];

	merge [[String]] is using: [
		['theosynth', 'model', Waveform],
		['base', 'math', as Math()],
		['base', 'struct', List],
		['base', 'audio', as Audio()],
		['base', 'core', SpecError],
		['base', 'sys', [AudioError, as Conditional(), as Loops()]]
	];

	Int is sampleRate: 44100;
	Array of Audio is devices: Array();
	Boolean is audioProbed: false;

	## Converts a [midi] note number (A4 = 69 = 440 Hz) to frequency in Hz.
	Function of Float is midiToFreq(Int is midi){
		return 440.0 * pow(base: 2.0, exp: toFloat(value: midi - 69) / 12.0);
	}

	## Evaluates [wave] at normalized phase [phase] in `[0.0, 1.0)`.
	Function of Float is sampleWave(Waveform is wave, Float is phase){
		if({ wave == Waveform:SQUARE }, {
			if({ phase < 0.5 }, { return 1.0; });
			return -1.0;
		});
		if({ wave == Waveform:SAWTOOTH }, {
			return 2.0 * phase - 1.0;
		});
		return sin(value: 6.283185307179586 * phase);
	}

	## Synthesizes a 16-bit signed little-endian stereo PCM buffer for [wave] at [freqHz].
	Function of List of Byte is synthesize(Waveform is wave, Float is freqHz, Int is durationMs: 160, Int is rate: 44100){
		local List of Byte is buf;
		local Int is totalSamples: (rate * durationMs) / 1000;
		local Int is fadeSamples: (rate * 12) / 1000;
		local Float is amplitude: 11000.0;
		local Float is phaseStep: freqHz / toFloat(value: rate);
		local Float is phase: 0.0;

		local Int is i: 0;
		while({ i < totalSamples }, {
			local Float is env: 1.0;
			if({ i < fadeSamples && fadeSamples > 0 }, {
				env: toFloat(value: i) / toFloat(value: fadeSamples);
			});
			if({ i > (totalSamples - fadeSamples) && fadeSamples > 0 }, {
				env: toFloat(value: totalSamples - i) / toFloat(value: fadeSamples);
			});
			local Float is val: sampleWave(wave: wave, phase: phase) * amplitude * env;
			local Int is s: toInt(value: round(value: val));
			if({ s < 0 }, { s: s + 65536; });
			local Byte is lo: (s & 255) as Byte;
			local Byte is hi: ((s >> 8) & 255) as Byte;
			buf:push(lo);
			buf:push(hi);
			buf:push(lo);
			buf:push(hi);
			phase: phase + phaseStep;
			if({ phase >= 1.0 }, { phase: phase - 1.0; });
			i: i + 1;
		});
		return buf;
	}

	local Function is ensureAudio(){
		if({ audioProbed }, { return; });
		audioProbed: true;
		local String is errMsg: '';
		local Audio is dev: Audio:open(
			sampleRate: sampleRate,
			channels: 2,
			format: 1,
			onError: local Function(SpecError of AudioError is error){
				errMsg: error:description;
			}
		);
		if({ errMsg == '' }, {
			devices: Array([dev]);
		});
	}

	## Plays [midi] with [wave] if an audio device is available (no-op in headless environments).
	Function is playMidi(Int is midi, Waveform is wave){
		ensureAudio();
		if({ devices:length() == 0 }, { return; });
		local List of Byte is pcm: synthesize(wave: wave, freqHz: midiToFreq(midi: midi), durationMs: 140, rate: sampleRate);
		devices:get(index: 0):write(samples: pcm, onError: local Function(SpecError of AudioError is _err){});
	}

	Function is close(){
		if({ devices:length() > 0 }, {
			devices:get(index: 0):close();
			devices: Array();
		});
		audioProbed: false;
	}
}
