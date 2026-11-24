#! Package theosynth:model
#! Common contract for synthesizer instruments in TheoSynth.

Class is Instrument{
	replace [String] is namespace: ['theosynth', 'model'];

	merge [[String]] is using: [
		['theosynth', 'model', [Waveform, InstrumentVoice]],
		['base', 'math', as Math()],
		['base', 'struct', List],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	Function of Waveform is waveform(){ Waveform:SINE }

	Function of String is name(){ 'Sine' }

	Function of InstrumentVoice is createVoice(Int is midi, Float is freqHz, Int is sampleRate){
		InstrumentVoice(midi: midi, step: freqHz / toFloat(value: sampleRate), initialEnv: 0.0)
	}

	## Synthesizes a 16-bit signed little-endian stereo PCM buffer at [freqHz] for [durationMs].
	Function of List of Byte is synthesize(Float is freqHz, Int is durationMs: 160, Int is rate: 22050){
		local List of Byte is buf;
		local Int is totalSamples: (rate * durationMs) / 1000;
		local Int is fadeSamples: (rate * 12) / 1000;
		local Float is amplitude: 11000.0;
		local InstrumentVoice is v: createVoice(midi: 69, freqHz: freqHz, sampleRate: rate);

		local Int is i: 0;
		while({ i < totalSamples }, {
			local Float is envK: 1.0;
			if({ i > (totalSamples - fadeSamples) && fadeSamples > 0 }, {
				envK: toFloat(value: totalSamples - i) / toFloat(value: fadeSamples);
			});
			local Float is sVal: v:nextSample() * amplitude * envK;
			local Int is s: toInt(value: round(value: sVal));
			if({ s < -32768 }, { s: -32768; });
			if({ s > 32767 }, { s: 32767; });
			if({ s < 0 }, { s: s + 65536; });
			local Byte is lo: (s & 255) as Byte;
			local Byte is hi: ((s >> 8) & 255) as Byte;
			buf:push(lo);
			buf:push(hi);
			buf:push(lo);
			buf:push(hi);
			i: i + 1;
		});
		v:destroy();
		return buf;
	}
}
