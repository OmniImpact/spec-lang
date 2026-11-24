#! Package theosynth:model
#! Real-time non-blocking polyphonic PCM synthesizer (Sine, Square, Sawtooth).

Class is SynthEngine{
	replace [String] is namespace: ['theosynth', 'model'];

	merge [[String]] is using: [
		['theosynth', 'model', Waveform],
		['base', 'math', as Math()],
		['base', 'struct', List],
		['base', 'audio', as Audio()],
		['base', 'core', SpecError],
		['base', 'sys', [AudioError, as Thread(), as Mem(), as Conditional(), as Loops()]],
		['base', 'sys', 'thread', ThreadScope]
	];

	Int is sampleRate: 22050;
	Int is mutex: 0;
	Boolean is running: false;

	[Int] is voiceMidi: [];
	[Int] is voiceWave: [];
	[Float] is voicePhase: [];
	[Float] is voiceStep: [];
	[Float] is voiceEnv: [];
	[Int] is voiceGate: [];

	replace Function is init(){
		mutex: mutexCreate();
	}

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

	local Function of Int is waveToInt(Waveform is w){
		if({ w == Waveform:SQUARE }, { return 1; });
		if({ w == Waveform:SAWTOOTH }, { return 2; });
		return 0;
	}

	local Function of Float is sampleWaveId(Int is wid, Float is phase){
		if({ wid == 1 }, {
			if({ phase < 0.5 }, { return 1.0; });
			return -1.0;
		});
		if({ wid == 2 }, {
			return 2.0 * phase - 1.0;
		});
		return sin(value: 6.283185307179586 * phase);
	}

	## Synthesizes a 16-bit signed little-endian stereo PCM buffer for [wave] at [freqHz].
	Function of List of Byte is synthesize(Waveform is wave, Float is freqHz, Int is durationMs: 160, Int is rate: 22050){
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

	## Triggers or retriggers [midi] with [wave] without blocking the UI thread.
	Function is noteOn(Int is midi, Waveform is wave){
		local Float is step: midiToFreq(midi: midi) / toFloat(value: sampleRate);
		local Int is wid: waveToInt(w: wave);
		mutexLock(handle: mutex);
		local Int is found: -1;
		local Int is i: 0;
		while({ i < voiceMidi:length() && found < 0 }, {
			if({ voiceMidi:get(index: i) == midi }, { found: i; });
			i: i + 1;
		});
		if({ found >= 0 }, {
			voiceWave:set(index: found, item: wid);
			voiceStep:set(index: found, item: step);
			voiceGate:set(index: found, item: 1);
		}, {
			local Int is slot: -1;
			local Int is j: 0;
			while({ j < voiceGate:length() && slot < 0 }, {
				if({ voiceGate:get(index: j) == 0 && voiceEnv:get(index: j) <= 0.001 }, { slot: j; });
				j: j + 1;
			});
			if({ slot >= 0 }, {
				voiceMidi:set(index: slot, item: midi);
				voiceWave:set(index: slot, item: wid);
				voicePhase:set(index: slot, item: 0.0);
				voiceStep:set(index: slot, item: step);
				voiceEnv:set(index: slot, item: 0.0);
				voiceGate:set(index: slot, item: 1);
			}, {
				voiceMidi:push(item: midi);
				voiceWave:push(item: wid);
				voicePhase:push(item: 0.0);
				voiceStep:push(item: step);
				voiceEnv:push(item: 0.0);
				voiceGate:push(item: 1);
			});
		});
		mutexUnlock(handle: mutex);
	}

	## Begins smooth release of [midi].
	Function is noteOff(Int is midi){
		mutexLock(handle: mutex);
		local Int is i: 0;
		while({ i < voiceMidi:length() }, {
			if({ voiceMidi:get(index: i) == midi }, {
				voiceGate:set(index: i, item: 0);
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

	## Renders [frames] stereo PCM frames by combining all active voices with equal-power polyphonic normalization.
	Function is mixChunk(List of Byte is outBuf, Int is frames){
		outBuf:clear();
		local Float is attackStep: 1.0 / 176.0;
		local Float is releaseStep: 1.0 / 440.0;
		local Float is amp: 14000.0;

		mutexLock(handle: mutex);
		local Int is nv: voiceMidi:length();
		local Int is fi: 0;
		while({ fi < frames }, {
			local Float is sumL: 0.0;
			local Float is sumR: 0.0;
			local Int is activeCount: 0;
			local Int is vi: 0;
			while({ vi < nv }, {
				local Int is gate: voiceGate:get(index: vi);
				local Float is env: voiceEnv:get(index: vi);
				if({ gate == 1 }, {
					env: env + attackStep;
					if({ env > 1.0 }, { env: 1.0; });
					voiceEnv:set(index: vi, item: env);
				}, {
					if({ env > 0.0 }, {
						env: env - releaseStep;
						if({ env < 0.0 }, { env: 0.0; });
						voiceEnv:set(index: vi, item: env);
					});
				});
				if({ env > 0.0005 }, {
					local Float is ph: voicePhase:get(index: vi);
					local Float is osc: sampleWaveId(wid: voiceWave:get(index: vi), phase: ph) * env;
					sumL: sumL + osc;
					sumR: sumR + osc;
					activeCount: activeCount + 1;
					ph: ph + voiceStep:get(index: vi);
					if({ ph >= 1.0 }, { ph: ph - 1.0; });
					voicePhase:set(index: vi, item: ph);
				});
				vi: vi + 1;
			});

			local Float is norm: if({ activeCount > 1 }, { 1.0 / sqrt(value: toFloat(value: activeCount)) }, { 1.0 });
			local Float is chL: sumL * norm;
			local Float is chR: sumR * norm;
			chL: chL / (1.0 + abs(value: chL) * 0.25);
			chR: chR / (1.0 + abs(value: chR) * 0.25);
			pushSample16(outBuf: outBuf, sample: chL * amp);
			pushSample16(outBuf: outBuf, sample: chR * amp);
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
