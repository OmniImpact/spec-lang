#! Package theosynth:model
#! Real-time polyphonic audio mixer and voice-pool host over [Instrument] implementations.

Class is SynthEngine{
	replace [String] is namespace: ['theosynth', 'model'];

	merge [[String]] is using: [
		['theosynth', 'model', [Instrument, InstrumentVoice, InstrumentRegistry, Waveform]],
		['base', 'math', as Math()],
		['base', 'struct', List],
		['base', 'audio', as Audio()],
		['base', 'core', SpecError],
		['base', 'sys', [AudioError, as Thread(), as Conditional(), as Loops()]],
		['base', 'sys', 'thread', ThreadScope]
	];

	Int is sampleRate: 22050;
	Int is mutex: 0;
	Boolean is running: false;
	Float is normGain: 1.0;

	InstrumentRegistry is registry: InstrumentRegistry();
	Array of InstrumentVoice is voices: Array();

	replace Function is init(){
		mutex: mutexCreate();
	}

	## Converts a [midi] note number (A4 = 69 = 440 Hz) to frequency in Hz.
	Function of Float is midiToFreq(Int is midi){
		return 440.0 * pow(base: 2.0, exp: toFloat(value: midi - 69) / 12.0);
	}

	## Synthesizes a 16-bit signed little-endian stereo PCM buffer for [wave] at [freqHz].
	Function of List of Byte is synthesize(Waveform is wave, Float is freqHz, Int is durationMs: 160, Int is rate: 22050){
		return registry:findByWaveform(wave: wave):synthesize(freqHz: freqHz, durationMs: durationMs, rate: rate);
	}

	## Triggers or retriggers [midi] using [instrument] without blocking the UI thread.
	Function is noteOnInstrument(Int is midi, Instrument is instrument){
		local Float is freq: midiToFreq(midi: midi);
		local InstrumentVoice is nextVoice: instrument:createVoice(midi: midi, freqHz: freq, sampleRate: sampleRate);

		mutexLock(handle: mutex);
		local Int is found: -1;
		local Int is i: 0;
		while({ i < voices:length() && found < 0 }, {
			if({ voices:get(index: i):midi == midi }, { found: i; });
			i: i + 1;
		});
		if({ found >= 0 }, {
			voices:get(index: found):destroy();
			voices:set(index: found, item: nextVoice);
		}, {
			local Int is slot: -1;
			local Int is j: 0;
			while({ j < voices:length() && slot < 0 }, {
				local InstrumentVoice is v: voices:get(index: j);
				if({ v:gate == 0 && v:env <= 0.001 }, { slot: j; });
				j: j + 1;
			});
			if({ slot >= 0 }, {
				voices:get(index: slot):destroy();
				voices:set(index: slot, item: nextVoice);
			}, {
				voices:add(item: nextVoice);
			});
		});
		mutexUnlock(handle: mutex);
	}

	## Triggers [midi] by looking up [wave] in [registry].
	Function is noteOn(Int is midi, Waveform is wave){
		noteOnInstrument(midi: midi, instrument: registry:findByWaveform(wave: wave));
	}

	## Begins smooth release of [midi] (respecting minimum attack hold so fast taps still sound).
	Function is noteOff(Int is midi){
		mutexLock(handle: mutex);
		local Int is i: 0;
		while({ i < voices:length() }, {
			local InstrumentVoice is v: voices:get(index: i);
			if({ v:midi == midi }, {
				if({ v:holdFrames > 0 }, {
					v:relPending: 1;
				}, {
					v:gate: 0;
				});
			});
			i: i + 1;
		});
		mutexUnlock(handle: mutex);
	}

	local Function is pushSample16(List of Byte is outBuf, Float is sample){
		local Int is s: toInt(value: round(value: sample));
		if({ s < -32768 }, { s: -32768; });
		if({ s > 32767 }, { s: 32767; });
		if({ s < 0 }, { s: s + 65536; });
		outBuf:push((s & 255) as Byte);
		outBuf:push(((s >> 8) & 255) as Byte);
	}

	## Renders [frames] stereo PCM frames by combining all active voices with linear equal-power normalization.
	Function is mixChunk(List of Byte is outBuf, Int is frames){
		outBuf:clear();
		local Float is attackStep: 1.0 / 176.0;
		local Float is releaseStep: 1.0 / 440.0;
		local Float is amp: 14000.0;

		mutexLock(handle: mutex);
		local Int is nv: voices:length();
		local Int is fi: 0;
		while({ fi < frames }, {
			local Float is sum: 0.0;
			local Int is activeCount: 0;
			local Int is vi: 0;
			while({ vi < nv }, {
				local InstrumentVoice is v: voices:get(index: vi);
				if({ v:holdFrames > 0 }, {
					v:holdFrames: v:holdFrames - 1;
					if({ v:holdFrames == 0 && v:relPending == 1 }, {
						v:gate: 0;
						v:relPending: 0;
					});
				});
				if({ v:gate == 1 }, {
					v:env: v:env + attackStep;
					if({ v:env > 1.0 }, { v:env: 1.0; });
				}, {
					if({ v:env > 0.0 }, {
						v:env: v:env - releaseStep;
						if({ v:env < 0.0 }, { v:env: 0.0; });
					});
				});
				if({ v:env > 0.0005 }, {
					sum: sum + v:nextSample() * v:env;
					activeCount: activeCount + 1;
				});
				vi: vi + 1;
			});

			local Float is targetGain: if({ activeCount > 1 }, { 1.0 / toFloat(value: activeCount) }, { 1.0 });
			normGain: normGain + (targetGain - normGain) * 0.04;
			local Float is out: sum * normGain * amp;
			pushSample16(outBuf: outBuf, sample: out);
			pushSample16(outBuf: outBuf, sample: out);
			fi: fi + 1;
		});
		mutexUnlock(handle: mutex);
	}

	## Starts the low-latency background audio mixer thread inside [scope].
	Function is startAudio(ThreadScope is scope){
		mutexLock(handle: mutex);
		if({ running }, {
			mutexUnlock(handle: mutex);
			return;
		});
		running: true;
		mutexUnlock(handle: mutex);

		scope:spawn(task: local Function(){
			local String is errMsg: '';
			local Audio is dev: Audio:open(
				sampleRate: sampleRate,
				channels: 2,
				format: 1,
				onError: local Function(SpecError of AudioError is error){
					errMsg: error:description;
				}
			);
			if({ errMsg != '' }, { return; });

			local List of Byte is chunkBuf;
			local Int is chunkFrames: 220;
			while({ true }, {
				mutexLock(handle: mutex);
				local Boolean is keepGoing: running;
				mutexUnlock(handle: mutex);
				if({ !keepGoing }, {
					dev:close();
					return;
				});
				mixChunk(outBuf: chunkBuf, frames: chunkFrames);
				dev:write(samples: chunkBuf, onError: local Function(SpecError of AudioError is _err){});
			});
		});
	}

	Function is close(){
		if({ mutex != 0 }, {
			mutexLock(handle: mutex);
			running: false;
			mutexUnlock(handle: mutex);
		});
	}
}
